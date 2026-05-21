import pytest

from app.config import Settings
from app.db.base import init_db, make_engine, make_session_factory
from app.db.factory import build_stores
from app.db.stores import SqlAssetLog, SqlSessionStore, SqlVoiceProfileStore
from app.services.memory import (
    InMemoryAssetLog,
    MarketingAsset,
)
from app.services.voice_profile import InMemoryVoiceProfileStore
from app.session import InMemorySessionStore


@pytest.fixture
def session_factory(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/test.db")
    init_db(engine)
    return make_session_factory(engine)


def test_voice_store_roundtrip_and_upsert(session_factory):
    store = SqlVoiceProfileStore(session_factory)
    assert store.get("u1") is None
    store.save("u1", {"tone": "dry"})
    assert store.get("u1") == {"tone": "dry"}
    store.save("u1", {"tone": "warm"})  # upsert
    assert store.get("u1") == {"tone": "warm"}


def test_asset_log_orders_and_summarizes(session_factory):
    log = SqlAssetLog(session_factory)
    assert log.list_for("u1") == []
    log.add(
        MarketingAsset(
            user_id="u1",
            asset_type="landing_page",
            marketing_angle="speed",
            created_at="2026-01-01T00:00:00+00:00",
        )
    )
    log.add(
        MarketingAsset(
            user_id="u1",
            asset_type="email_promo",
            metrics={"opens": 42},
            created_at="2026-02-01T00:00:00+00:00",
        )
    )
    log.add(MarketingAsset(user_id="other", asset_type="ad"))

    assets = log.list_for("u1")
    assert [a.asset_type for a in assets] == ["landing_page", "email_promo"]
    summary = log.summarize("u1")
    assert "2 prior asset(s)" in summary
    assert "opens=42" in summary
    assert "angle: speed" in summary


def test_session_store_set_get_reset(session_factory):
    store = SqlSessionStore(session_factory)
    assert store.get("s1") == {}
    store.set("s1", {"next_step": "diagnose", "messages": [{"role": "user", "content": "hi"}]})
    got = store.get("s1")
    assert got["next_step"] == "diagnose"
    assert got["messages"][0]["content"] == "hi"
    store.set("s1", {"next_step": "refine"})  # upsert replaces
    assert store.get("s1")["next_step"] == "refine"
    store.reset("s1")
    assert store.get("s1") == {}


def test_build_stores_selects_backend(tmp_path):
    in_mem = build_stores(Settings(database_url=None))
    assert isinstance(in_mem[0], InMemoryVoiceProfileStore)
    assert isinstance(in_mem[1], InMemoryAssetLog)
    assert isinstance(in_mem[2], InMemorySessionStore)

    sql = build_stores(Settings(database_url=f"sqlite:///{tmp_path}/x.db"))
    assert isinstance(sql[0], SqlVoiceProfileStore)
    assert isinstance(sql[1], SqlAssetLog)
    assert isinstance(sql[2], SqlSessionStore)
