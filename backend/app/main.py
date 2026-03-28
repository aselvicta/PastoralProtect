import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.cycle import router as cycle_router
from app.api.routes.demo import router as demo_router
from app.api.routes.oracle import router as oracle_router
from app.api.routes.payments import router as payments_router
from app.api.routes.policies import router as policies_router
from app.api.routes.storage import router as storage_router
from app.api.routes.ussd import router as ussd_router
from app.api.routes.webhooks import router as webhooks_router
from app.api.routes.zones import router as zones_router
from app.bootstrap import run_migrations, seed_demo_users, seed_demo_zones
from app.core.config import settings

logger = logging.getLogger("pastoralprotect.api")


def _cors_origins() -> list[str]:
    raw = settings.cors_allowed_origins.strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    run_migrations()
    seed_demo_zones()
    seed_demo_users()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    if not request.url.path.startswith("/api"):
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s %.1fms", request.method, request.url.path, response.status_code, ms)
    return response

app.include_router(auth_router, prefix="/api")
app.include_router(policies_router, prefix="/api")
app.include_router(zones_router, prefix="/api")
app.include_router(oracle_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(storage_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(cycle_router, prefix="/api")
app.include_router(ussd_router, prefix="/api")


@app.get("/")
def root() -> dict:
    """Root URL so opening http://127.0.0.1:8000/ is not a bare 404."""
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "hint": "API routes are under /api/... Open /docs to try auth and endpoints. UI: http://localhost:3000",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "pastoral-protect-api"}
