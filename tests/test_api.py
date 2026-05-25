import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_JWT_SECRET, auth_header


@pytest.fixture
def client():
    # Force offline FakeLLM and enable auth with the test signing secret.
    app = create_app(Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET))
    return TestClient(app)


def test_health_is_public(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["offline"] is True


def test_cors_preflight_allows_apex_www_and_vercel(client):
    # The /chat/stream preflight must succeed for the apex domain, www, and Vercel
    # previews — a 400 here is what breaks the browser chat + admin calls.
    for origin in (
        "https://mythostack.com",
        "https://www.mythostack.com",
        "https://chatoy-jvj0hqaax-v3ads-projects.vercel.app",
    ):
        r = client.options(
            "/chat/stream",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert r.status_code in (200, 204), (origin, r.status_code)
        assert r.headers.get("access-control-allow-origin") == origin


def test_me_reports_admin_flag(client):
    admin = client.get("/me", headers=auth_header("a", email="vipaymanshalaby@gmail.com")).json()
    assert admin["is_admin"] is True
    normal = client.get("/me", headers=auth_header("b", email="x@y.com")).json()
    assert normal["is_admin"] is False


def test_chat_diagnose_then_handoff_flow(client):
    h = auth_header("u1")
    r1 = client.post("/chat", json={"session_id": "s1", "message": "I need marketing help"}, headers=h)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["next_step"] == "diagnose"
    assert "?" in body1["reply"]
    assert body1["current_strategy"] is None

    r2 = client.post("/chat", json={"session_id": "s1", "message": "More trial signups"}, headers=h)
    body2 = r2.json()
    assert body2["next_step"] == "refine"
    assert body2["current_strategy"]["asset_type"] == "email_promo"
    assert "Subject:" in body2["reply"]
    assert "PROMPT_HANDOFF" not in body2["reply"]
    assert body2["retrieved_frameworks"]


def _parse_sse(text: str) -> list[tuple[str, str]]:
    events = []
    event = "message"
    for line in text.splitlines():
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            events.append((event, line.split(":", 1)[1].strip()))
            event = "message"
    return events


def test_chat_stream_emits_tokens_and_final(client):
    h = auth_header("u9")
    r1 = client.post("/chat/stream", json={"session_id": "s2", "message": "help me grow"}, headers=h)
    assert r1.status_code == 200
    events = _parse_sse(r1.text)
    kinds = [k for k, _ in events]
    assert "token" in kinds and "final" in kinds and "done" in kinds
    assert "?" in "".join(d for k, d in events if k == "token")

    r2 = client.post("/chat/stream", json={"session_id": "s2", "message": "more signups"}, headers=h)
    events2 = _parse_sse(r2.text)
    tokens2 = "".join(d for k, d in events2 if k == "token")
    assert "PROMPT_HANDOFF" not in tokens2
    final = json.loads([d for k, d in events2 if k == "final"][0])
    assert final["current_strategy"]["asset_type"] == "email_promo"


def test_voice_analyze_and_get(client):
    h = auth_header("u2")
    r = client.post("/voice/analyze", json={"samples": ["Here's the thing. I write short."]}, headers=h)
    assert r.status_code == 200
    assert r.json()["profile"]
    assert r.json()["rendered"]

    assert client.get("/voice/me", headers=h).status_code == 200
    # A different user has no profile yet.
    assert client.get("/voice/me", headers=auth_header("nobody")).status_code == 404


def test_billing_checkout_400_when_stripe_unconfigured(client):
    h = auth_header("u4")
    # No Stripe key in the test settings → graceful 400, never a crash.
    r = client.post("/billing/checkout", json={"kind": "credits"}, headers=h)
    assert r.status_code == 400
    assert client.get("/credits", headers=h).json()["credits_balance"] >= 0


def test_assets_log_and_list(client):
    h = auth_header("u3")
    r = client.post(
        "/assets",
        json={"asset_type": "email_promo", "marketing_angle": "speed", "metrics": {"opens": 10}},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["asset_type"] == "email_promo"
    assert r.json()["user_id"] == "u3"

    body = client.get("/assets", headers=h).json()
    assert len(body["assets"]) == 1
    assert "opens=10" in body["summary"]
