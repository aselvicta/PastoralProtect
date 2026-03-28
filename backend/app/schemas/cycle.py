from typing import Literal, Optional

from pydantic import BaseModel, Field


class CyclePhaseOut(BaseModel):
    """One box in the README architecture diagram (lines 34–60)."""

    id: str
    label: str
    status: Literal["complete", "pending", "failed", "skipped"]
    detail: str


class CycleStatusOut(BaseModel):
    phases: list[CyclePhaseOut]
    storage_backend: Literal["mock", "storacha", "legacy_http"]
    chain_configured: bool
    cycle_complete: bool = Field(
        description="True when every required phase is complete; optional chain may be skipped."
    )
