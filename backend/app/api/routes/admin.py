from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import AdminUser, DbSession
from app.core.config import settings
from app.models.db_models import Farmer, NdviReading, OracleExecutionLog, Payout, Policy, TriggerEvent
from app.schemas.admin import PoolStatusOut, RecentEventItem
from app.schemas.impact import ImpactOut
from app.services.contract_service import contract_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pool-status", response_model=PoolStatusOut)
def pool_status(db: DbSession, _: AdminUser) -> dict[str, Any]:
    total = db.scalar(select(func.count()).select_from(Policy)) or 0
    active = db.scalar(
        select(func.count()).select_from(Policy).where(Policy.status == "active")
    ) or 0
    prem = db.scalar(select(func.coalesce(func.sum(Policy.premium_amount), 0))) or 0
    pay_sum = db.scalar(select(func.coalesce(func.sum(Payout.amount), 0))) or 0
    pay_done = db.scalar(
        select(func.count()).select_from(Payout).where(Payout.status == "completed")
    ) or 0
    latest_trig = db.execute(select(TriggerEvent).order_by(TriggerEvent.created_at.desc()).limit(1)).scalar_one_or_none()
    latest_any = db.execute(
        select(Payout).order_by(Payout.created_at.desc()).limit(1)
    ).scalar_one_or_none()

    latest_trigger_dict = None
    if latest_trig:
        latest_trigger_dict = {
            "zone_db_id": latest_trig.zone_db_id,
            "week": latest_trig.week,
            "breached": latest_trig.breached,
            "ndvi": latest_trig.ndvi_value,
            "threshold": latest_trig.threshold,
            "tx_hash": latest_trig.tx_hash,
            "storage_cid": latest_trig.storage_cid,
            "verification_passed": latest_trig.verification_passed,
            "at": latest_trig.created_at.isoformat(),
        }

    chain = contract_service.pool_metrics()

    return {
        "total_policies": int(total),
        "active_policies": int(active),
        "total_premiums_mock_tzs": int(prem),
        "total_payouts_mock_tzs": int(pay_sum),
        "total_payouts_completed": int(pay_done),
        "latest_trigger": latest_trigger_dict,
        "contract_address": settings.contract_address or None,
        "latest_tx_hash": (latest_any.tx_hash if latest_any else None) or (
            latest_trig.tx_hash if latest_trig else None
        ),
        "chain_premiums_wei": chain["premiums_wei"] if chain else None,
        "chain_payouts_recorded": chain["payouts_recorded"] if chain else None,
        "chain_active_policies": chain["active_policies"] if chain else None,
    }


@router.get("/impact", response_model=ImpactOut)
def impact_metrics(db: DbSession, _: AdminUser) -> ImpactOut:
    farmers = db.scalar(select(func.count()).select_from(Farmer)) or 0
    livestock = db.scalar(
        select(func.coalesce(func.sum(Policy.livestock_count), 0)).where(Policy.status == "active")
    ) or 0
    payouts_n = db.scalar(select(func.count()).select_from(Payout).where(Payout.status == "completed")) or 0
    droughts = db.scalar(
        select(func.count()).select_from(TriggerEvent).where(TriggerEvent.breached.is_(True))
    ) or 0
    ndvi_n = db.scalar(select(func.count()).select_from(NdviReading)) or 0
    return ImpactOut(
        total_farmers_enrolled=int(farmers),
        total_livestock_protected=int(livestock),
        total_payouts_executed=int(payouts_n),
        drought_events_detected=int(droughts),
        ndvi_snapshots_archived=int(ndvi_n),
    )


@router.get("/recent-events", response_model=list[RecentEventItem])
def recent_events(db: DbSession, _: AdminUser) -> list[RecentEventItem]:
    items: list[RecentEventItem] = []
    triggers = db.execute(select(TriggerEvent).order_by(TriggerEvent.created_at.desc()).limit(8)).scalars().all()
    for t in triggers:
        items.append(
            RecentEventItem(
                type="trigger",
                at=t.created_at,
                summary=f"Zone {t.zone_db_id} week {t.week} breached={t.breached}",
                payload={
                    "ndvi": t.ndvi_value,
                    "threshold": t.threshold,
                    "tx_hash": t.tx_hash,
                    "storage_cid": t.storage_cid,
                    "content_sha256": t.content_sha256,
                    "verification_passed": t.verification_passed,
                },
            )
        )
    payouts = db.execute(select(Payout).order_by(Payout.created_at.desc()).limit(8)).scalars().all()
    for p in payouts:
        items.append(
            RecentEventItem(
                type="payout",
                at=p.created_at,
                summary=f"Payout {p.id} farmer {p.farmer_id} amount {p.amount}",
                payload={
                    "reference": p.provider_reference,
                    "status": p.status,
                    "tx_hash": p.tx_hash,
                    "storage_cid": p.storage_cid,
                },
            )
        )
    oracle = db.execute(
        select(OracleExecutionLog).order_by(OracleExecutionLog.created_at.desc()).limit(6)
    ).scalars().all()
    for o in oracle:
        items.append(
            RecentEventItem(
                type="oracle",
                at=o.created_at,
                summary=o.action_taken,
                payload={"success": o.success, "error": o.error_message},
            )
        )

    items.sort(key=lambda x: x.at, reverse=True)
    return items[:20]
