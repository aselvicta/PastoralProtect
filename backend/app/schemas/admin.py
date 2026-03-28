from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class PoolStatusOut(BaseModel):
    total_policies: int
    active_policies: int
    total_premiums_mock_tzs: int
    total_payouts_mock_tzs: int
    total_payouts_completed: int
    latest_trigger: Optional[dict[str, Any]] = None
    contract_address: Optional[str] = None
    latest_tx_hash: Optional[str] = None
    chain_premiums_wei: Optional[str] = None
    chain_payouts_recorded: Optional[str] = None
    chain_active_policies: Optional[int] = None


class RecentEventItem(BaseModel):
    type: str
    at: datetime
    summary: str
    payload: dict[str, Any] = {}
