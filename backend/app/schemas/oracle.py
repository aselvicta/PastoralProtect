from typing import Any, Optional

from pydantic import BaseModel, Field


class OracleSimulateRequest(BaseModel):
    zone_id: str = Field(..., min_length=1)
    ndvi_value: float = Field(..., ge=-0.2, le=1.0)
    week: int = Field(..., ge=1, le=53)


class OracleSimulateResult(BaseModel):
    breached: bool
    zone_id: str
    week: int
    ndvi_value: float
    threshold: float
    trigger_tx_hash: Optional[str] = None
    payouts_created: list[dict[str, Any]]
    chain_error: Optional[str] = None
    message: str
    content_sha256: Optional[str] = None
    storage_cid: Optional[str] = None
    verification_passed: Optional[bool] = None
    verification_detail: Optional[str] = None


class OracleWebhookPayload(BaseModel):
    zone_id: str
    current_ndvi: float = Field(..., alias="currentNdvi")
    week: int
    signature_mock: Optional[str] = None

    class Config:
        populate_by_name = True
