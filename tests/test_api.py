import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    # Force offline FakeLLM regardless of any ambient API key.
    app = create_app(Settings(use_fake_llm=True))
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["offline"] is True


def test_chat_diagnose_then_handoff_flow(client):
    r1 = client.post(
        "/chat",
        json={"session_id": "s1", "user_id": "u1", "message": "I need marketing help"},
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["next_step"] == "diagnose"
    assert "?" in body1["reply"]
    assert body1["current_strategy"] is None

    r2 = client.post(
        "/chat",
        json={"session_id": "s1", "user_id": "u1", "message": "More trial signups"},
    )
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
    # First turn streams the CRO question.
    r1 = client.post(
        "/chat/stream",
        json={"session_id": "s2", "user_id": "u9", "message": "help me grow"},
    )
    assert r1.status_code == 200
    events = _parse_sse(r1.text)
    kinds = [k for k, _ in events]
    assert "token" in kinds
    assert "final" in kinds
    assert "done" in kinds
    tokens = "".join(d for k, d in events if k == "token")
    assert "?" in tokens

    # Second turn triggers handoff -> streams the written copy, never the marker.
    r2 = client.post(
        "/chat/stream",
        json={"session_id": "s2", "user_id": "u9", "message": "more signups"},
    )
    events2 = _parse_sse(r2.text)
    tokens2 = "".join(d for k, d in events2 if k == "token")
    assert "PROMPT_HANDOFF" not in tokens2
    final = [d for k, d in events2 if k == "final"][0]
    final_payload = json.loads(final)
    assert final_payload["current_strategy"]["asset_type"] == "email_promo"


def test_voice_analyze_and_get(client):
    r = client.post(
        "/voice/analyze",
        json={"user_id": "u2", "samples": ["Here's the thing. I write short. Punchy."]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]  # non-empty fingerprint
    assert body["rendered"]

    r2 = client.get("/voice/u2")
    assert r2.status_code == 200

    assert client.get("/voice/does-not-exist").status_code == 404


def test_assets_log_and_list(client):
    r = client.post(
        "/assets",
        json={
            "user_id": "u3",
            "asset_type": "email_promo",
            "marketing_angle": "speed",
            "metrics": {"opens": 10},
        },
    )
    assert r.status_code == 200
    assert r.json()["asset_type"] == "email_promo"

    r2 = client.get("/assets/u3")
    body = r2.json()
    assert len(body["assets"]) == 1
    assert "opens=10" in body["summary"]
