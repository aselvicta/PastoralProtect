from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.cycle import CycleStatusOut
from app.services.cycle_service import cycle_status_snapshot

router = APIRouter(prefix="/cycle", tags=["cycle"])


@router.get("/status", response_model=CycleStatusOut)
def get_cycle_status(db: DbSession, _: AdminUser) -> CycleStatusOut:
    """README diagram (ingress → IPFS → oracle → optional chain → mock payouts) as checkable phases."""
    return cycle_status_snapshot(db)
