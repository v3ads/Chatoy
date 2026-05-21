import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from app.auth import JWTAuth, build_auth
from app.config import Settings
from app.main import create_app
from tests.conftest import make_es256_token


def _client_with_key(public_key):
    # Inject an asymmetric verifier whose key comes from a local resolver,
    # standing in for the Supabase JWKS fetch.
    auth = JWTAuth(
        signing_key_resolver=lambda _token: public_key,
        algorithms=["ES256"],
        audience="authenticated",
    )
    return TestClient(create_app(Settings(use_fake_llm=True), auth=auth))


def test_asymmetric_token_accepted_and_scoped():
    priv = ec.generate_private_key(ec.SECP256R1())
    client = _client_with_key(priv.public_key())

    token = make_es256_token("alice", priv)
    r = client.post(
        "/assets",
        json={"asset_type": "email_promo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["user_id"] == "alice"


def test_asymmetric_token_with_wrong_key_rejected():
    priv = ec.generate_private_key(ec.SECP256R1())
    other_pub = ec.generate_private_key(ec.SECP256R1()).public_key()
    client = _client_with_key(other_pub)

    token = make_es256_token("alice", priv)
    r = client.get("/assets", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_asymmetric_missing_token_rejected():
    priv = ec.generate_private_key(ec.SECP256R1())
    client = _client_with_key(priv.public_key())
    assert client.get("/assets").status_code == 401


def test_build_auth_selects_jwks_mode_from_supabase_url():
    auth = build_auth(Settings(supabase_url="https://abc123.supabase.co"))
    assert auth._asymmetric is True
    assert auth.jwks_url == "https://abc123.supabase.co/auth/v1/.well-known/jwks.json"
    assert auth.issuer == "https://abc123.supabase.co/auth/v1"
    assert "ES256" in auth.algorithms and "RS256" in auth.algorithms


def test_build_auth_falls_back_to_hs256_secret():
    auth = build_auth(Settings(jwt_secret="a-shared-secret-that-is-long-enough-1234"))
    assert auth._asymmetric is False
    assert auth.algorithms == ["HS256"]


def test_build_auth_unconfigured_is_not_configured():
    auth = build_auth(Settings())
    assert auth.configured is False


def _jwks_for(public_key, kid="k1"):
    jwk = json.loads(ECAlgorithm(ECAlgorithm.SHA256).to_jwk(public_key))
    jwk.update({"kid": kid, "use": "sig", "alg": "ES256"})
    return {"keys": [jwk]}


def _serve_jwks(jwks: dict) -> ThreadingHTTPServer:
    body = json.dumps(jwks).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_real_jwks_client_fetches_and_verifies():
    # Exercises the actual PyJWKClient path (fetch JWKS, match kid, ES256
    # verify) against a local stand-in for the Supabase JWKS endpoint.
    priv = ec.generate_private_key(ec.SECP256R1())
    server = _serve_jwks(_jwks_for(priv.public_key(), kid="k1"))
    try:
        port = server.server_address[1]
        auth = JWTAuth(jwks_url=f"http://127.0.0.1:{port}/jwks.json")
        token = make_es256_token("alice", priv, kid="k1")
        principal = auth.authenticate(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        )
        assert principal.user_id == "alice"

        # A token signed by an unknown key (no matching kid) is rejected.
        other = ec.generate_private_key(ec.SECP256R1())
        bad = make_es256_token("alice", other, kid="unknown")
        with pytest.raises(HTTPException) as exc:
            auth.authenticate(
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=bad)
            )
        assert exc.value.status_code == 401
    finally:
        server.shutdown()
