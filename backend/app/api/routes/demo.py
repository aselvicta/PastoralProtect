import logging
import uuid
from typing import Any

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.api.deps import DbSession, DemoRunner
from app.api.routes import policies as policies_routes
from app.schemas.policies import EnrollRequest
from app.services.cycle_service import cycle_status_snapshot
from app.services.oracle_service import oracle_service

router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger(__name__)


@router.post("/run")
async def run_full_demo(db: DbSession, _: DemoRunner) -> dict[str, Any]:
    """
    One-click hackathon flow: sample farmer → enroll → NDVI shock → oracle + Filecoin + payouts.
    Protected by admin JWT unless DEMO_PUBLIC_ACCESS=true.
    """
    farmer_id = f"DEMO-{uuid.uuid4().hex[:10]}"
    enroll_body = EnrollRequest(
        farmer_id=farmer_id,
        phone_number="+255700DEMO01",
        zone_id="Z1",
        livestock_count=12,
        premium_amount=4000,
        preferred_language="sw",
    )
    enroll_res = await run_in_threadpool(policies_routes.enroll, enroll_body, db)

    week = 22
    ndvi = 0.11
    oracle_data = await oracle_service.process_zone_ndvi(db, "Z1", ndvi, week)

    refs = [p.get("mock_reference") for p in oracle_data.get("payouts_created", []) if p.get("mock_reference")]

    logger.info(
        "demo.run_ok farmer_id=%s cid=%s refs=%s",
        farmer_id,
        oracle_data.get("storage_cid"),
        len(refs),
    )

    snap = cycle_status_snapshot(db)

    return {
        "message": "Demo flow completed",
        "steps": [
            {"step": 1, "label": "Sample farmer + enrollment", "farmer_id": farmer_id},
            {"step": 2, "label": "Oracle / NDVI shock", "week": week, "ndvi": ndvi},
            {"step": 3, "label": "Verifiable bundle + Filecoin CID", "cid": oracle_data.get("storage_cid")},
            {"step": 4, "label": "Mock mobile money references", "references": refs},
        ],
        "enrollment": enroll_res.model_dump(mode="json"),
        "oracle": oracle_data,
        "cycle": snap.model_dump(mode="json"),
    }
