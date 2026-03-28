import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.security import create_access_token, verify_password
from app.models.db_models import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    username = body.username.strip()
    u = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if u is None or not verify_password(body.password, u.password_hash):
        logger.info("auth.login_failed username=%s", username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=u.username, role=u.role)
    logger.info("auth.login_ok username=%s role=%s", username, u.role)
    return TokenResponse(access_token=token, role=u.role)
