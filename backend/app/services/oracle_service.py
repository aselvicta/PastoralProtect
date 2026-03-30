from __future__ import annotations

import traceback
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db_models import (
    NdviReading,
    OracleExecutionLog,
    Payout,
    Policy,
    StorageUploadLog,
    TriggerEvent,
    Zone,
)
from app.services.contract_service import contract_service
from app.services.filecoin_storage_service import StorageUploadResult, filecoin_storage_service
from app.services.payment_service import payment_service


class OracleService:
    def _log_storage(
        self,
        db: Session,
        *,
        kind: str,
        entity_id: Optional[int],
        cid: Optional[str],
        sha: Optional[str],
        success: bool,
        detail: Optional[str] = None,
    ) -> None:
        db.add(
            StorageUploadLog(
                entity_kind=kind,
                entity_id=entity_id,
                cid=cid,
                content_sha256=sha,
                success=success,
                detail=detail,
            )
        )

    async def process_zone_ndvi(
        self,
        db: Session,
        zone_slug: str,
        ndvi_value: float,
        week: int,
    ) -> dict[str, Any]:
        zone = db.execute(select(Zone).where(Zone.zone_id == zone_slug)).scalar_one_or_none()
        if zone is None:
            raise ValueError("Zone not found")
        if not zone.is_active:
            raise ValueError("Zone inactive")

        threshold = float(zone.ndvi_threshold)
        breached = ndvi_value < threshold

        bundle: dict[str, Any] = {
            "protocol": "pastoralprotect-oracle-v1",
            "kind": "ndvi_trigger_bundle",
            "zone_id": zone.zone_id,
            "week": int(week),
            "ndvi_value": float(ndvi_value),
            "threshold": float(threshold),
            "breached": bool(breached),
        }

        bundle_up: StorageUploadResult
        try:
            bundle_up = await filecoin_storage_service.upload_json(f"oracle-{zone_slug}-w{week}", bundle)
            self._log_storage(
                db,
                kind="oracle_bundle",
                entity_id=None,
                cid=bundle_up.cid,
                sha=bundle_up.content_sha256,
                success=True,
                detail=(
                    f"storage_mode={bundle_up.storage_mode}"
                    + (f"; {bundle_up.warning}" if bundle_up.warning else "")
                ),
            )
        except Exception as e:  # noqa: BLE001
            self._log_storage(
                db,
                kind="oracle_bundle",
                entity_id=None,
                cid=None,
                sha=None,
                success=False,
                detail=str(e),
            )
            raise ValueError(f"Decentralized storage upload failed: {e!s}") from e

        cid = bundle_up.cid
        digest = bundle_up.content_sha256

        reading = NdviReading(
            zone_db_id=zone.id,
            week=week,
            ndvi_value=ndvi_value,
            source="oracle",
            content_sha256=digest,
            storage_cid=cid,
        )
        db.add(reading)
        db.flush()
        self._log_storage(
            db,
            kind="ndvi_reading",
            entity_id=reading.id,
            cid=cid,
            sha=digest,
            success=True,
        )

        trigger_tx_hash: Optional[str] = None
        payouts_payload: list[dict[str, Any]] = []
        chain_error: Optional[str] = None
        verification_passed: Optional[bool] = None
        verification_detail: Optional[str] = None

        trig = TriggerEvent(
            zone_db_id=zone.id,
            week=week,
            ndvi_value=ndvi_value,
            threshold=threshold,
            breached=breached,
            content_sha256=digest,
            storage_cid=cid,
        )
        db.add(trig)
        db.flush()

        if not breached:
            verification_passed = True
            verification_detail = "No payout path; integrity recorded on Filecoin/IPFS."
            trig.verification_passed = True
            trig.verification_detail = verification_detail
            db.add(
                OracleExecutionLog(
                    zone_db_id=zone.id,
                    week=week,
                    ndvi_value=ndvi_value,
                    action_taken="no_breach",
                    success=True,
                )
            )
            db.commit()
            return {
                "breached": False,
                "zone_id": zone.zone_id,
                "week": week,
                "ndvi_value": ndvi_value,
                "threshold": threshold,
                "trigger_tx_hash": None,
                "payouts_created": [],
                "chain_error": None,
                "message": "NDVI at or above threshold; no trigger.",
                "content_sha256": digest,
                "storage_cid": cid,
                "storage_mode": bundle_up.storage_mode,
                "storage_gateway_url": bundle_up.gateway_url,
                "storage_warning": bundle_up.warning,
                "verification_passed": verification_passed,
                "verification_detail": verification_detail,
            }

        ok, verr = await filecoin_storage_service.verify_cid_matches_hash(cid, digest)
        verification_passed = ok
        verification_detail = verr or "CID matches SHA256; verifiable trigger."
        trig.verification_passed = ok
        trig.verification_detail = verification_detail
        if not ok:
            db.add(
                OracleExecutionLog(
                    zone_db_id=zone.id,
                    week=week,
                    ndvi_value=ndvi_value,
                    action_taken="verification_failed",
                    success=False,
                    error_message=verr,
                )
            )
            db.commit()
            return {
                "breached": True,
                "zone_id": zone.zone_id,
                "week": week,
                "ndvi_value": ndvi_value,
                "threshold": threshold,
                "trigger_tx_hash": None,
                "payouts_created": [],
                "chain_error": None,
                "message": "Trigger rejected: verifiable data mismatch (possible tampering).",
                "content_sha256": digest,
                "storage_cid": cid,
                "storage_mode": bundle_up.storage_mode,
                "storage_gateway_url": bundle_up.gateway_url,
                "storage_warning": bundle_up.warning,
                "verification_passed": False,
                "verification_detail": verification_detail,
            }

        policies = list(
            db.execute(
                select(Policy).where(
                    Policy.zone_db_id == zone.id,
                    Policy.status == "active",
                )
            ).scalars().all()
        )

        eligible: list[Policy] = []
        for pol in policies:
            existing = db.execute(
                select(Payout).where(
                    Payout.policy_id == pol.id,
                    Payout.week == week,
                )
            ).scalar_one_or_none()
            if existing is None:
                eligible.append(pol)

        if not eligible:
            db.add(
                OracleExecutionLog(
                    zone_db_id=zone.id,
                    week=week,
                    ndvi_value=ndvi_value,
                    action_taken="breach_no_policies",
                    success=True,
                    error_message=None,
                )
            )
            db.commit()
            return {
                "breached": True,
                "zone_id": zone.zone_id,
                "week": week,
                "ndvi_value": ndvi_value,
                "threshold": threshold,
                "trigger_tx_hash": None,
                "payouts_created": [],
                "chain_error": None,
                "message": "Threshold breached; no active policies to pay.",
                "content_sha256": digest,
                "storage_cid": cid,
                "storage_mode": bundle_up.storage_mode,
                "storage_gateway_url": bundle_up.gateway_url,
                "storage_warning": bundle_up.warning,
                "verification_passed": True,
                "verification_detail": verification_detail,
            }

        contract_ids: list[int] = []
        amounts: list[int] = []
        for pol in eligible:
            amt = int(pol.livestock_count) * int(settings.payout_per_head)
            cid_p = pol.contract_policy_id
            if cid_p:
                contract_ids.append(int(cid_p))
                amounts.append(amt)

        if contract_service.enabled() and contract_ids:
            try:
                trigger_tx_hash = contract_service.validate_and_payout(
                    zone.contract_zone_id,
                    ndvi_value,
                    week,
                    contract_ids,
                    amounts,
                )
            except Exception as e:  # noqa: BLE001
                chain_error = str(e)
                traceback.print_exc()

        trig.tx_hash = trigger_tx_hash
        db.flush()

        for pol in eligible:
            amt = int(pol.livestock_count) * int(settings.payout_per_head)
            payout = Payout(
                policy_id=pol.id,
                farmer_id=pol.farmer_id,
                zone_db_id=zone.id,
                amount=amt,
                week=week,
                status="pending",
                provider="mock-mpesa",
                tx_hash=trigger_tx_hash,
            )
            db.add(payout)
            db.flush()
            ref, _ = await payment_service.execute_mock_payout(db, payout)
            pol.last_payout_week = week
            pay_payload = {
                "protocol": "pastoralprotect-payout-v1",
                "payout_id": payout.id,
                "policy_id": pol.id,
                "farmer_id": pol.farmer_id,
                "zone_id": zone.zone_id,
                "week": week,
                "amount": amt,
                "mock_reference": ref,
            }
            pur: StorageUploadResult | None = None
            try:
                pur = await filecoin_storage_service.upload_json(f"payout-{payout.id}", pay_payload)
                payout.storage_cid = pur.cid
                payout.content_sha256 = pur.content_sha256
                self._log_storage(
                    db,
                    kind="payout",
                    entity_id=payout.id,
                    cid=pur.cid,
                    sha=pur.content_sha256,
                    success=True,
                    detail=(
                        f"storage_mode={pur.storage_mode}"
                        + (f"; {pur.warning}" if pur.warning else "")
                    ),
                )
            except Exception as e:  # noqa: BLE001
                self._log_storage(
                    db,
                    kind="payout",
                    entity_id=payout.id,
                    cid=None,
                    sha=None,
                    success=False,
                    detail=str(e),
                )

            payouts_payload.append(
                {
                    "policy_db_id": pol.id,
                    "farmer_id": pol.farmer_id,
                    "amount": amt,
                    "mock_reference": ref,
                    "storage_cid": payout.storage_cid,
                    "storage_mode": pur.storage_mode if pur else None,
                    "storage_gateway_url": pur.gateway_url if pur else None,
                    "storage_warning": pur.warning if pur else None,
                }
            )

        oracle_ok = not (bool(contract_ids) and chain_error is not None)
        db.add(
            OracleExecutionLog(
                zone_db_id=zone.id,
                week=week,
                ndvi_value=ndvi_value,
                action_taken="trigger_and_payout",
                success=oracle_ok,
                error_message=chain_error,
            )
        )
        db.commit()

        msg = "Drought trigger processed; payouts simulated and archived to IPFS/Filecoin."
        if chain_error:
            msg = f"Chain note: {chain_error} (mock payouts + storage completed)."

        return {
            "breached": True,
            "zone_id": zone.zone_id,
            "week": week,
            "ndvi_value": ndvi_value,
            "threshold": threshold,
            "trigger_tx_hash": trigger_tx_hash,
            "payouts_created": payouts_payload,
            "chain_error": chain_error,
            "message": msg,
            "content_sha256": digest,
            "storage_cid": cid,
            "storage_mode": bundle_up.storage_mode,
            "storage_gateway_url": bundle_up.gateway_url,
            "storage_warning": bundle_up.warning,
            "verification_passed": True,
            "verification_detail": verification_detail,
        }


oracle_service = OracleService()
