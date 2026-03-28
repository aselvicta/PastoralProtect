"""
Maps deployment + DB state to the README pipeline (ingress → IPFS → oracle → optional chain → mock payouts).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db_models import NdviReading, Payout, TriggerEvent
from app.schemas.cycle import CyclePhaseOut, CycleStatusOut
from app.services.contract_service import contract_service


def _storage_backend() -> str:
    if (settings.storacha_uploader_url or "").strip() and (settings.storacha_uploader_secret or "").strip():
        return "storacha"
    if (settings.web3_storage_token or "").strip():
        return "legacy_http"
    return "mock"


def cycle_status_snapshot(db: Session) -> CycleStatusOut:
    n_readings = db.scalar(select(func.count()).select_from(NdviReading).where(NdviReading.storage_cid.isnot(None))) or 0
    n_triggers = db.scalar(select(func.count()).select_from(TriggerEvent)) or 0
    n_payouts_done = db.scalar(
        select(func.count()).select_from(Payout).where(Payout.status == "completed")
    ) or 0

    failed_verify = db.scalar(
        select(func.count())
        .select_from(TriggerEvent)
        .where(TriggerEvent.breached.is_(True), TriggerEvent.verification_passed.is_(False))
    ) or 0

    latest_trig = db.execute(select(TriggerEvent).order_by(TriggerEvent.created_at.desc()).limit(1)).scalar_one_or_none()
    chain_on = contract_service.enabled()

    # Optional chain: last on-chain signal
    has_chain_tx = bool(
        latest_trig
        and latest_trig.breached
        and latest_trig.tx_hash
        and (latest_trig.tx_hash or "").strip()
    )

    sb = _storage_backend()

    # 1 — Web / USSD / API
    p_api = CyclePhaseOut(
        id="ingress",
        label="Pastoralist / USSD / Web → FastAPI",
        status="complete",
        detail="Policies, zones, oracle, auth, and POST /api/ussd are live.",
    )

    # 2 — IPFS / Filecoin pin
    if n_readings > 0:
        p_ipfs = CyclePhaseOut(
            id="filecoin_pin",
            label="Canonical JSON + CID + hash (IPFS / Filecoin)",
            status="complete",
            detail=f"NDVI bundles archived ({sb} backend).",
        )
    else:
        p_ipfs = CyclePhaseOut(
            id="filecoin_pin",
            label="Canonical JSON + CID + hash (IPFS / Filecoin)",
            status="pending",
            detail="Run Simulate drought or Run full demo to create a pinned NDVI bundle.",
        )

    # 3 — Verifiable oracle
    if failed_verify > 0:
        p_oracle = CyclePhaseOut(
            id="verifiable_oracle",
            label="Verifiable oracle (fetch CID · SHA-256)",
            status="failed",
            detail="A breached trigger failed integrity check; payouts were blocked.",
        )
    elif n_triggers > 0:
        p_oracle = CyclePhaseOut(
            id="verifiable_oracle",
            label="Verifiable oracle (fetch CID · SHA-256)",
            status="complete",
            detail="Trigger events recorded; breach path verifies hash before payout.",
        )
    else:
        p_oracle = CyclePhaseOut(
            id="verifiable_oracle",
            label="Verifiable oracle (fetch CID · SHA-256)",
            status="pending",
            detail="No NDVI trigger in DB yet—simulate a reading or run the demo.",
        )

    # 4 — Solidity (optional)
    if not chain_on:
        p_chain = CyclePhaseOut(
            id="solidity_pool",
            label="PastoralProtectPool + web3.py (optional)",
            status="skipped",
            detail="Set BASE_RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY (+ artifact) to record txs on-chain.",
        )
    elif has_chain_tx:
        p_chain = CyclePhaseOut(
            id="solidity_pool",
            label="PastoralProtectPool + web3.py (optional)",
            status="complete",
            detail="Latest breached run includes a validateAndPayout tx hash.",
        )
    else:
        p_chain = CyclePhaseOut(
            id="solidity_pool",
            label="PastoralProtectPool + web3.py (optional)",
            status="pending",
            detail="Chain is configured; enroll policies on-chain so validateAndPayout can fire.",
        )

    # 5 — Mock mobile money + metrics
    if n_payouts_done > 0:
        p_pay = CyclePhaseOut(
            id="mock_mobile_money",
            label="Mock mobile money + admin metrics",
            status="complete",
            detail=f"{n_payouts_done} mock payout(s) completed; dashboard impact metrics update.",
        )
    else:
        p_pay = CyclePhaseOut(
            id="mock_mobile_money",
            label="Mock mobile money + admin metrics",
            status="pending",
            detail="Complete a breach with active policies to run mock M-Pesa references.",
        )

    phases = [p_api, p_ipfs, p_oracle, p_chain, p_pay]

    cycle_complete = (
        p_ipfs.status == "complete"
        and p_oracle.status == "complete"
        and p_chain.status in ("complete", "skipped")
        and p_pay.status == "complete"
    )

    return CycleStatusOut(
        phases=phases,
        storage_backend=sb,  # type: ignore[arg-type]
        chain_configured=chain_on,
        cycle_complete=cycle_complete,
    )

