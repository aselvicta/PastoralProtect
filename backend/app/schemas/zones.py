from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ZoneCreate(BaseModel):
    zone_id: str = Field(..., min_length=1, max_length=32)
    contract_zone_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)
    region: str = Field(..., min_length=1, max_length=255)
    ndvi_threshold: float = Field(..., gt=0, lt=1)
    is_active: bool = True


class ZonePatch(BaseModel):
    ndvi_threshold: Optional[float] = Field(default=None, gt=0, lt=1)
    is_active: Optional[bool] = None
    name: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=255)


class ZoneOut(BaseModel):
    id: int
    zone_id: str
    contract_zone_id: int
    name: str
    region: str
    ndvi_threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
