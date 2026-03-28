from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MockPayoutRequest(BaseModel):
    policy_id: int = Field(..., ge=1)
    amount: int = Field(..., ge=1)


class PaymentLogOut(BaseModel):
    id: int
    payout_id: int
    provider: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
