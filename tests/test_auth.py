import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_JWT_SECRET, auth_header, make_token


@pytest.fixture
def client():
    return TestClient(create_app(Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET)))


def test_protected_endpoints_require_a_token(client):
    assert client.post("/chat", json={"session_id": "s", "message": "hi"}).status_code == 401
    assert client.get("/assets").status_code == 401
    assert client.get("/voice/me").status_code == 401


def test_invalid_and_expired_tokens_rejected(client):
    assert client.get("/assets", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401
    # Wrong signing secret.
    bad = make_token("u1", secret="a-different-secret-that-is-also-long-enough")
    assert client.get("/assets", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    # Expired.
    expired = make_token("u1", exp_delta=-10)
    assert client.get("/assets", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_health_needs_no_token(client):
    assert client.get("/health").status_code == 200


def test_assets_are_isolated_per_tenant(client):
    a, b = auth_header("alice"), auth_header("bob")
    client.post("/assets", json={"asset_type": "email_promo", "metrics": {"opens": 5}}, headers=a)

    assert len(client.get("/assets", headers=a).json()["assets"]) == 1
    # Bob sees none of Alice's assets.
    assert client.get("/assets", headers=b).json()["assets"] == []


def test_voice_profiles_are_isolated_per_tenant(client):
    a, b = auth_header("alice"), auth_header("bob")
    client.post("/voice/analyze", json={"samples": ["punchy. short."]}, headers=a)
    assert client.get("/voice/me", headers=a).status_code == 200
    assert client.get("/voice/me", headers=b).status_code == 404


def test_sessions_are_isolated_per_tenant(client):
    a, b = auth_header("alice"), auth_header("bob")
    # Both use the same session_id but must get independent conversations.
    client.post("/chat", json={"session_id": "shared", "message": "first"}, headers=a)
    client.post("/chat", json={"session_id": "shared", "message": "second"}, headers=a)

    # Bob's very first turn on the same session_id is still a fresh diagnose.
    r = client.post("/chat", json={"session_id": "shared", "message": "hello"}, headers=b)
    assert r.json()["next_step"] == "diagnose"
    assert r.json()["current_strategy"] is None


def test_auth_disabled_mode_uses_dev_user(client):
    dev = TestClient(create_app(Settings(use_fake_llm=True, auth_disabled=True)))
    # No token needed; everything maps to the dev user.
    r = dev.post("/assets", json={"asset_type": "ad"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "dev-user"


def test_unconfigured_auth_fails_closed():
    # Auth on, but no secret provided -> 503 (fail closed), not silent bypass.
    misconfigured = TestClient(create_app(Settings(use_fake_llm=True, jwt_secret=None)))
    assert misconfigured.get("/assets", headers=auth_header("u1")).status_code == 503
