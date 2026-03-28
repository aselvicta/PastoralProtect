from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token

DbSession = Annotated[Session, Depends(get_db)]

security = HTTPBearer(auto_error=False)


class AuthUser:
    __slots__ = ("username", "role")

    def __init__(self, username: str, role: str) -> None:
        self.username = username
        self.role = role


def get_bearer_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[AuthUser]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_token(credentials.credentials)
        sub = str(payload.get("sub", ""))
        role = str(payload.get("role", ""))
        if not sub or not role:
            return None
        return AuthUser(sub, role)
    except Exception:
        return None


def _legacy_admin_ok(x_admin_key: Optional[str]) -> bool:
    return bool(x_admin_key and settings.admin_api_key and x_admin_key == settings.admin_api_key)


def require_admin_access(
    x_admin_key: Annotated[Optional[str], Header(alias="X-Admin-Key")] = None,
    bearer: Annotated[Optional[AuthUser], Depends(get_bearer_user)] = None,
) -> AuthUser:
    if _legacy_admin_ok(x_admin_key):
        return AuthUser("legacy-admin", "ADMIN")
    if bearer is not None and bearer.role == "ADMIN":
        return bearer
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin authentication required")


def require_oracle_access(
    bearer: Annotated[Optional[AuthUser], Depends(get_bearer_user)] = None,
    x_oracle_secret: Annotated[Optional[str], Header(alias="X-Oracle-Secret")] = None,
) -> AuthUser:
    if x_oracle_secret and x_oracle_secret == settings.oracle_secret:
        return AuthUser("legacy-oracle", "ORACLE")
    if bearer is not None and bearer.role in ("ORACLE", "ADMIN"):
        return bearer
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Oracle authentication required")


def require_demo_runner(
    x_admin_key: Annotated[Optional[str], Header(alias="X-Admin-Key")] = None,
    bearer: Annotated[Optional[AuthUser], Depends(get_bearer_user)] = None,
) -> AuthUser:
    if settings.demo_public_access:
        return AuthUser("public-demo", "ADMIN")
    return require_admin_access(x_admin_key=x_admin_key, bearer=bearer)


# Annotated shortcuts for routers
AdminUser = Annotated[AuthUser, Depends(require_admin_access)]
OracleUser = Annotated[AuthUser, Depends(require_oracle_access)]
DemoRunner = Annotated[AuthUser, Depends(require_demo_runner)]
