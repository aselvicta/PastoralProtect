import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import db_models  # noqa: F401  — register tables
from app.core.security import hash_password
from app.models.db_models import User, Zone

logger = logging.getLogger(__name__)


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
    """Upsert users whose SEED_*_PASSWORD is set in the environment (see backend/.env.example)."""
    specs: list[tuple[str, str, str]] = [
        ("judge_demo", settings.seed_judge_demo_password, "ADMIN"),
        ("admin", settings.seed_admin_password, "ADMIN"),
        ("oracle", settings.seed_oracle_password, "ORACLE"),
        ("farmer", settings.seed_farmer_password, "USER"),
    ]
    db = SessionLocal()
    try:
        seeded: list[str] = []
        for username, plain, role in specs:
            if not (plain or "").strip():
                continue
            u = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
            h = hash_password(plain.strip())
            if u is None:
                db.add(User(username=username, password_hash=h, role=role))
            else:
                u.password_hash = h
                u.role = role
            seeded.append(username)
        db.commit()
        if not seeded:
            logger.warning(
                "No demo users seeded: all SEED_*_PASSWORD values are empty. "
                "Set at least SEED_JUDGE_DEMO_PASSWORD in backend/.env (see .env.example)."
            )
        elif "judge_demo" not in seeded:
            logger.warning(
                "judge_demo not seeded: SEED_JUDGE_DEMO_PASSWORD is empty. "
                "Dashboard demo quick sign-in will fail until it is set."
            )
    finally:
        db.close()
