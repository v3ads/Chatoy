from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

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
    """Verifies Supabase bearer JWTs.

    Two verification modes:
      - Asymmetric (current Supabase default): a JWKS URL provides public keys;
        tokens are verified with ES256/RS256 by matching the token's ``kid``.
      - Legacy HS256: a shared ``secret``.

    ``signing_key_resolver`` lets tests (or custom setups) supply the
    verification key for a token directly, bypassing network JWKS fetches.
    """

    def __init__(
        self,
        *,
        secret: str | None = None,
        jwks_url: str | None = None,
        audience: str = "authenticated",
        issuer: str | None = None,
        algorithms: list[str] | None = None,
        disabled: bool = False,
        dev_user: str = "dev-user",
        signing_key_resolver: Callable[[str], object] | None = None,
    ) -> None:
        self.secret = secret
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer
        self.disabled = disabled
        self.dev_user = dev_user
        self._signing_key_resolver = signing_key_resolver

        self._asymmetric = bool(jwks_url) or signing_key_resolver is not None
        self.algorithms = algorithms or (
            ["ES256", "RS256"] if self._asymmetric else ["HS256"]
        )

        self._jwks_client = None
        if jwks_url and signing_key_resolver is None:
            from jwt import PyJWKClient

            self._jwks_client = PyJWKClient(jwks_url)

    @property
    def configured(self) -> bool:
        return self.disabled or self._asymmetric or bool(self.secret)

    def _verification_key(self, token: str):
        if self._signing_key_resolver is not None:
            return self._signing_key_resolver(token)
        if self._jwks_client is not None:
            return self._jwks_client.get_signing_key_from_jwt(token).key
        return self.secret

    def authenticate(self, credentials: HTTPAuthorizationCredentials | None) -> Principal:
        if self.disabled:
            return Principal(user_id=self.dev_user, claims={"sub": self.dev_user})

        if not self.configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Auth is not configured (set CHATOY_SUPABASE_URL, "
                    "CHATOY_JWT_SECRET, or CHATOY_AUTH_DISABLED)."
                ),
            )

        if credentials is None or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        try:
            key = self._verification_key(token)
            decode_kwargs: dict = {
                "algorithms": self.algorithms,
                "audience": self.audience,
                "options": {"require": ["exp", "sub"]},
            }
            if self.issuer:
                decode_kwargs["issuer"] = self.issuer
            claims = jwt.decode(token, key, **decode_kwargs)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as exc:  # JWKS fetch / key resolution failures
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not verify token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sub = claims.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject"
            )
        return Principal(user_id=str(sub), email=claims.get("email"), claims=claims)


def build_auth(settings: Settings) -> JWTAuth:
    explicit_algos = [a.strip() for a in settings.jwt_algorithms.split(",") if a.strip()]
    jwks_url = settings.resolved_jwks_url

    if jwks_url:
        # Honor an explicit non-default algorithm list, else use asymmetric defaults.
        algorithms = explicit_algos if explicit_algos and explicit_algos != ["HS256"] else None
        return JWTAuth(
            jwks_url=jwks_url,
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            algorithms=algorithms,
            disabled=settings.auth_disabled,
            dev_user=settings.dev_user_id,
        )

    return JWTAuth(
        secret=settings.jwt_secret,
        audience=settings.jwt_audience,
        algorithms=explicit_algos or ["HS256"],
        disabled=settings.auth_disabled,
        dev_user=settings.dev_user_id,
    )
