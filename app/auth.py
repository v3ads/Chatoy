from __future__ import annotations

from dataclasses import dataclass, field

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings

# auto_error=False so we can return our own 401 with a clear message rather than
# FastAPI's generic "Not authenticated".
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    """The authenticated caller. ``user_id`` is the token subject and the tenant
    boundary every query is scoped to."""

    user_id: str
    email: str | None = None
    claims: dict = field(default_factory=dict)


class JWTAuth:
    def __init__(
        self,
        *,
        secret: str | None,
        audience: str = "authenticated",
        algorithms: list[str] | None = None,
        disabled: bool = False,
        dev_user: str = "dev-user",
    ) -> None:
        self.secret = secret
        self.audience = audience
        self.algorithms = algorithms or ["HS256"]
        self.disabled = disabled
        self.dev_user = dev_user

    def authenticate(self, credentials: HTTPAuthorizationCredentials | None) -> Principal:
        if self.disabled:
            return Principal(user_id=self.dev_user, claims={"sub": self.dev_user})

        if not self.secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth is not configured (set CHATOY_JWT_SECRET or CHATOY_AUTH_DISABLED).",
            )

        if credentials is None or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            claims = jwt.decode(
                credentials.credentials,
                self.secret,
                algorithms=self.algorithms,
                audience=self.audience,
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sub = claims.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject"
            )
        return Principal(user_id=str(sub), email=claims.get("email"), claims=claims)


def build_auth(settings: Settings) -> JWTAuth:
    algorithms = [a.strip() for a in settings.jwt_algorithms.split(",") if a.strip()]
    return JWTAuth(
        secret=settings.jwt_secret,
        audience=settings.jwt_audience,
        algorithms=algorithms or ["HS256"],
        disabled=settings.auth_disabled,
        dev_user=settings.dev_user_id,
    )
