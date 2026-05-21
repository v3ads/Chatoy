import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import init_db, make_engine, make_session_factory
from app.db.stores import SqlAssetLog, SqlSessionStore, SqlVoiceProfileStore
from app.main import create_app
from tests.conftest import TEST_JWT_SECRET, auth_header


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path}/api.db"


def _stores(db_url):
    engine = make_engine(db_url)
    init_db(engine)
    sf = make_session_factory(engine)
    return SqlVoiceProfileStore(sf), SqlAssetLog(sf), SqlSessionStore(sf)


def _app(db_url):
    voice, assets, sessions = _stores(db_url)
    settings = Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET)
    return TestClient(
        create_app(settings, voice_store=voice, asset_log=assets, session_store=sessions)
    )


def test_state_survives_a_restart(db_url):
    h = auth_header("u1")

    # --- First "process": drive a session to handoff and log results. ---
    c1 = _app(db_url)
    c1.post("/chat", json={"session_id": "s1", "message": "grow me"}, headers=h)
    r = c1.post("/chat", json={"session_id": "s1", "message": "more signups"}, headers=h)
    assert r.json()["next_step"] == "refine"
    c1.post("/voice/analyze", json={"samples": ["short. punchy. no fluff."]}, headers=h)
    c1.post("/assets", json={"asset_type": "email_promo", "metrics": {"opens": 99}}, headers=h)

    # --- Second "process": brand-new app + stores on the same database. ---
    c2 = _app(db_url)

    assert c2.get("/voice/me", headers=h).status_code == 200

    assets = c2.get("/assets", headers=h).json()
    assert len(assets["assets"]) == 1
    assert "opens=99" in assets["summary"]

    # Conversation state persisted: continuing the session keeps prior turns.
    r2 = c2.post("/chat", json={"session_id": "s1", "message": "make it punchier"}, headers=h)
    body = r2.json()
    assert body["next_step"] == "refine"
    assert len(body["new_messages"]) == 1
