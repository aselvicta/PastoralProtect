from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EnrollRequest(BaseModel):
    farmer_id: str = Field(..., min_length=1, max_length=64)
    phone_number: str = Field(..., min_length=5, max_length=32)
    zone_id: str = Field(..., min_length=1, max_length=32)
    livestock_count: int = Field(..., ge=1)
    premium_amount: int = Field(..., ge=1, description="Mock TZS premium")
    preferred_language: str = Field(default="sw", max_length=8)
    wallet_address: Optional[str] = Field(default=None, max_length=128)


class EnrollResponse(BaseModel):
    policy: "PolicyOut"
    enrollment_message: str
    contract_tx_hash: Optional[str] = None


class PolicyOut(BaseModel):
    id: int
    farmer_id: str
    zone_id: str
    livestock_count: int
    premium_amount: int
    status: str
    enrolled_at: datetime
    last_payout_week: Optional[int]
    contract_policy_id: Optional[int]
    enroll_tx_hash: Optional[str]
    phone_number: Optional[str]

    class Config:
        from_attributes = True


EnrollResponse.model_rebuild()
