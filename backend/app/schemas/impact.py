from pydantic import BaseModel


class ImpactOut(BaseModel):
    total_farmers_enrolled: int
    total_livestock_protected: int
    total_payouts_executed: int
    drought_events_detected: int
    ndvi_snapshots_archived: int
