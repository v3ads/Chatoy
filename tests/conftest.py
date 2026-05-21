import time

import jwt

TEST_JWT_SECRET = "test-secret-not-for-production-0123456789"


def make_token(
    user_id: str,
    *,
    email: str | None = None,
    secret: str = TEST_JWT_SECRET,
    audience: str = "authenticated",
    exp_delta: int = 3600,
) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "aud": audience, "iat": now, "exp": now + exp_delta}
    if email:
        payload["email"] = email
    return jwt.encode(payload, secret, algorithm="HS256")


def auth_header(user_id: str, **kwargs) -> dict:
    return {"Authorization": f"Bearer {make_token(user_id, **kwargs)}"}


def make_es256_token(
    user_id: str,
    private_key,
    *,
    kid: str = "test-key",
    audience: str = "authenticated",
    issuer: str | None = None,
    email: str | None = None,
    exp_delta: int = 3600,
) -> str:
    """Mint an asymmetric (ES256) token, mirroring Supabase signing keys."""
    now = int(time.time())
    payload = {"sub": user_id, "aud": audience, "iat": now, "exp": now + exp_delta}
    if issuer:
        payload["iss"] = issuer
    if email:
        payload["email"] = email
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})
