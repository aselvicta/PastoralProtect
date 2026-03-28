import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.db_models import Farmer, Policy, Zone
from app.schemas.policies import EnrollRequest, EnrollResponse, PolicyOut
from app.services.contract_service import contract_service

router = APIRouter(prefix="/policies", tags=["policies"])
logger = logging.getLogger(__name__)


def _policy_out(p: Policy, zone_slug: str) -> PolicyOut:
    return PolicyOut(
        id=p.id,
        farmer_id=p.farmer_id,
        zone_id=zone_slug,
        livestock_count=p.livestock_count,
        premium_amount=p.premium_amount,
        status=p.status,
        enrolled_at=p.enrolled_at,
        last_payout_week=p.last_payout_week,
        contract_policy_id=p.contract_policy_id,
        enroll_tx_hash=p.enroll_tx_hash,
        phone_number=p.phone_number,
    )


@router.post("/enroll", response_model=EnrollResponse)
def enroll(body: EnrollRequest, db: DbSession) -> EnrollResponse:
    zone = db.execute(select(Zone).where(Zone.zone_id == body.zone_id)).scalar_one_or_none()
    if zone is None or not zone.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive zone")

    existing = db.execute(
        select(Policy).where(
            Policy.farmer_id == body.farmer_id,
            Policy.zone_db_id == zone.id,
            Policy.status == "active",
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Active policy already exists for this farmer in zone")

    farmer = db.execute(select(Farmer).where(Farmer.farmer_id == body.farmer_id)).scalar_one_or_none()
    if farmer is None:
        farmer = Farmer(
            farmer_id=body.farmer_id,
            phone_number=body.phone_number,
            preferred_language=body.preferred_language,
            wallet_address=body.wallet_address,
        )
        db.add(farmer)
        db.flush()
    else:
        farmer.phone_number = body.phone_number
        farmer.preferred_language = body.preferred_language
        if body.wallet_address:
            farmer.wallet_address = body.wallet_address

    policy = Policy(
        farmer_id=body.farmer_id,
        zone_db_id=zone.id,
        livestock_count=body.livestock_count,
        premium_amount=body.premium_amount,
        status="active",
        phone_number=body.phone_number,
    )
    db.add(policy)
    db.flush()

    tx_hash: Optional[str] = None
    cid: Optional[int] = None
    msg = "Umepata udhaifu wa mifugo. Nambari ya sera: " + str(policy.id)

    if contract_service.enabled():
        try:
            tx_hash, cid = contract_service.enroll_policy(
                body.farmer_id,
                zone.contract_zone_id,
                body.livestock_count,
                body.wallet_address,
            )
            if cid:
                policy.contract_policy_id = cid
            policy.enroll_tx_hash = tx_hash
            db.commit()
            msg += f". Mnukuu wa mnyororo: {tx_hash[:16]}..."
        except Exception as e:  # noqa: BLE001
            db.commit()
            msg += f". Hifadhri: mnyororo haujatingwa ({e!s})."
    else:
        db.commit()

    db.refresh(policy)
    logger.info(
        "policy.enrolled farmer_id=%s zone=%s policy_db_id=%s",
        body.farmer_id,
        body.zone_id,
        policy.id,
    )
    return EnrollResponse(
        policy=_policy_out(policy, zone.zone_id),
        enrollment_message=msg,
        contract_tx_hash=tx_hash,
    )


@router.get("", response_model=list[PolicyOut])
def list_policies(db: DbSession) -> list[PolicyOut]:
    rows = db.execute(select(Policy)).scalars().all()
    out: list[PolicyOut] = []
    for p in rows:
        z = db.get(Zone, p.zone_db_id)
        out.append(_policy_out(p, z.zone_id if z else ""))
    return out


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: int, db: DbSession) -> PolicyOut:
    p = db.get(Policy, policy_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    z = db.get(Zone, p.zone_db_id)
    return _policy_out(p, z.zone_id if z else "")
