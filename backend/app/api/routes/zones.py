from fastapi import APIRouter, HTTPException

from app.api.deps import AdminUser, DbSession
from app.models.db_models import Zone
from app.schemas.zones import ZoneCreate, ZoneOut, ZonePatch
from app.services.contract_service import contract_service
from sqlalchemy import select

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
def list_zones(db: DbSession) -> list[ZoneOut]:
    return list(db.execute(select(Zone)).scalars().all())


@router.post("", response_model=ZoneOut)
def create_zone(body: ZoneCreate, db: DbSession, _: AdminUser) -> Zone:
    exists = db.execute(select(Zone).where(Zone.zone_id == body.zone_id)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="zone_id already exists")
    exists_c = db.execute(select(Zone).where(Zone.contract_zone_id == body.contract_zone_id)).scalar_one_or_none()
    if exists_c:
        raise HTTPException(status_code=409, detail="contract_zone_id already exists")
    z = Zone(
        zone_id=body.zone_id,
        contract_zone_id=body.contract_zone_id,
        name=body.name,
        region=body.region,
        ndvi_threshold=body.ndvi_threshold,
        is_active=body.is_active,
    )
    db.add(z)
    db.commit()
    db.refresh(z)

    if contract_service.enabled():
        try:
            contract_service.add_zone_chain(
                z.contract_zone_id,
                z.name,
                z.ndvi_threshold,
                z.is_active,
            )
        except Exception:
            pass
    return z


@router.patch("/{zone_id}", response_model=ZoneOut)
def patch_zone(zone_id: str, body: ZonePatch, db: DbSession, _: AdminUser) -> Zone:
    z = db.execute(select(Zone).where(Zone.zone_id == zone_id)).scalar_one_or_none()
    if z is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    if body.ndvi_threshold is not None:
        z.ndvi_threshold = body.ndvi_threshold
    if body.is_active is not None:
        z.is_active = body.is_active
    if body.name is not None:
        z.name = body.name
    if body.region is not None:
        z.region = body.region
    db.commit()
    db.refresh(z)

    if contract_service.enabled() and body.ndvi_threshold is not None:
        try:
            contract_service.update_zone_threshold_chain(z.contract_zone_id, z.ndvi_threshold)
        except Exception:
            pass
    return z
