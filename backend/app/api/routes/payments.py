from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.models.db_models import PaymentLog, Payout, Policy
from app.schemas.payments import MockPayoutRequest, PaymentLogOut
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/mock-payout")
async def mock_payout(body: MockPayoutRequest, db: DbSession, _: AdminUser) -> dict:
    p = db.get(Policy, body.policy_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Policy not found — use policy DB id")
    payout = Payout(
        policy_id=p.id,
        farmer_id=p.farmer_id,
        zone_db_id=p.zone_db_id,
        amount=body.amount,
        week=0,
        status="pending",
        provider="mock-mpesa",
    )
    db.add(payout)
    db.flush()
    ref, st = await payment_service.execute_mock_payout(db, payout)
    db.commit()
    return {"reference": ref, "status": st, "payout_id": payout.id}


@router.get("/logs", response_model=list[PaymentLogOut])
def payment_logs(db: DbSession, _: AdminUser) -> list[PaymentLogOut]:
    rows = db.execute(select(PaymentLog).order_by(PaymentLog.created_at.desc())).scalars().all()
    return list(rows)
