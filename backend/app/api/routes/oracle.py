from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession, OracleUser
from app.core.config import settings
from app.schemas.oracle import OracleSimulateRequest, OracleSimulateResult
from app.services.oracle_service import oracle_service

router = APIRouter(prefix="/oracle", tags=["oracle"])


@router.post("/simulate", response_model=OracleSimulateResult)
async def simulate(body: OracleSimulateRequest, db: DbSession, _: OracleUser) -> OracleSimulateResult:
    try:
        data = await oracle_service.process_zone_ndvi(db, body.zone_id, body.ndvi_value, body.week)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return OracleSimulateResult.model_validate(data)
