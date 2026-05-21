import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import init_db, make_engine, make_session_factory
from app.db.stores import SqlAssetLog, SqlSessionStore, SqlVoiceProfileStore
from app.main import create_app


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
    settings = Settings(use_fake_llm=True)
    return TestClient(
        create_app(
            settings,
            voice_store=voice,
            asset_log=assets,
            session_store=sessions,
        )
    )


def test_state_survives_a_restart(db_url):
    # --- First "process": drive a session to handoff and log results. ---
    c1 = _app(db_url)
    c1.post("/chat", json={"session_id": "s1", "user_id": "u1", "message": "grow me"})
    r = c1.post("/chat", json={"session_id": "s1", "user_id": "u1", "message": "more signups"})
    assert r.json()["next_step"] == "refine"
    c1.post(
        "/voice/analyze",
        json={"user_id": "u1", "samples": ["short. punchy. no fluff."]},
    )
    c1.post(
        "/assets",
        json={"user_id": "u1", "asset_type": "email_promo", "metrics": {"opens": 99}},
    )

    # --- Second "process": brand-new app + stores on the same database. ---
    c2 = _app(db_url)

    # Voice profile persisted.
    assert c2.get("/voice/u1").status_code == 200

    # Asset + metrics persisted.
    assets = c2.get("/assets/u1").json()
    assert len(assets["assets"]) == 1
    assert "opens=99" in assets["summary"]

    # Conversation state persisted: continuing the session keeps prior turns
    # and routes a refine straight to the writer.
    r2 = c2.post(
        "/chat", json={"session_id": "s1", "user_id": "u1", "message": "make it punchier"}
    )
    body = r2.json()
    assert body["next_step"] == "refine"
    # The persisted history (4 prior messages) is still there before this turn.
    assert len(body["new_messages"]) == 1
