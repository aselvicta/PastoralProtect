from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import db_models  # noqa: F401  — register tables
from app.core.security import hash_password
from app.models.db_models import User, Zone


def run_migrations() -> None:
    Base.metadata.create_all(bind=engine)


def seed_demo_zones() -> None:
    db = SessionLocal()
    try:
        n = db.execute(select(Zone)).scalars().first()
        if n is not None:
            return
        zones = [
            Zone(
                zone_id="Z1",
                contract_zone_id=1,
                name="Arusha Kaskazini",
                region="Arusha",
                ndvi_threshold=0.35,
                is_active=True,
            ),
            Zone(
                zone_id="Z2",
                contract_zone_id=2,
                name="Manyara Mashariki",
                region="Manyara",
                ndvi_threshold=0.38,
                is_active=True,
            ),
            Zone(
                zone_id="Z3",
                contract_zone_id=3,
                name="Shinyanga Magharibi",
                region="Shinyanga",
                ndvi_threshold=0.40,
                is_active=True,
            ),
        ]
        db.add_all(zones)
        db.commit()
    finally:
        db.close()


def seed_demo_users() -> None:
    """Ensure demo accounts exist with known passwords (upsert). Fixes stale DBs / hash scheme changes."""
    db = SessionLocal()
    try:
        demo_rows = [
            ("admin", "Admin123!", "ADMIN"),
            ("oracle", "Oracle123!", "ORACLE"),
            ("farmer", "User123!", "USER"),
        ]
        for username, plain, role in demo_rows:
            u = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
            h = hash_password(plain)
            if u is None:
                db.add(User(username=username, password_hash=h, role=role))
            else:
                u.password_hash = h
                u.role = role
        db.commit()
    finally:
        db.close()
