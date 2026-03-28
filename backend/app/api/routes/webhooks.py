from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import AuthUser, DbSession, get_bearer_user, require_oracle_access
from app.core.config import settings
from app.schemas.oracle import OracleSimulateResult, OracleWebhookPayload
from app.services.oracle_service import oracle_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/oracle", response_model=OracleSimulateResult)
async def oracle_webhook(
    body: OracleWebhookPayload,
    db: DbSession,
    bearer: Annotated[Optional[AuthUser], Depends(get_bearer_user)] = None,
    x_oracle_secret: Annotated[Optional[str], Header(alias="X-Oracle-Secret")] = None,
) -> OracleSimulateResult:
    if body.signature_mock != settings.oracle_secret:
        require_oracle_access(bearer=bearer, x_oracle_secret=x_oracle_secret)
    try:
        data = await oracle_service.process_zone_ndvi(db, body.zone_id, body.current_ndvi, body.week)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return OracleSimulateResult.model_validate(data)
