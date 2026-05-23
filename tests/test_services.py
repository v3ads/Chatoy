import json

from app.llm.fake import FakeLLM
from app.services.memory import InMemoryAssetLog, MarketingAsset
from app.services.rag import InMemoryFrameworkRetriever
from app.services.voice_profile import (
    InMemoryVoiceProfileStore,
    analyze_voice,
    render_voice_profile,
)


def test_rag_returns_asset_specific_frameworks():
    # Contract: retrieval is keyed by asset type and respects k.
    rag = InMemoryFrameworkRetriever({"email_promo": ["A", "B", "C"]})
    assert rag.retrieve("email_promo", k=2) == ["A", "B"]

    # The built-in library returns dedicated (non-generic) email frameworks.
    from app.services.rag import _GENERIC

    default_out = InMemoryFrameworkRetriever().retrieve("email_promo", k=2)
    assert len(default_out) == 2
    assert default_out != _GENERIC[:2]


def test_rag_loose_match_and_generic_fallback():
    rag = InMemoryFrameworkRetriever()
    assert rag.retrieve("promotional email")  # loose-matches email_promo
    generic = rag.retrieve("something_unknown")
    assert generic and any("AIDA" in f for f in generic)


def test_analyze_voice_parses_json_profile():
    profile_json = json.dumps({"tone": "playful", "jargon_level": "low"})
    llm = FakeLLM(responder=lambda system, messages: profile_json)
    profile = analyze_voice(llm, ["some sample text"])
    assert profile["tone"] == "playful"


def test_analyze_voice_empty_samples_returns_empty():
    llm = FakeLLM(responder=lambda s, m: "{}")
    assert analyze_voice(llm, ["   ", ""]) == {}


def test_render_voice_profile_formats_lists():
    rendered = render_voice_profile(
        {"tone": "warm", "signature_phrases": ["here's the thing", "let's go"]}
    )
    assert "Tone: warm" in rendered
    assert "here's the thing, let's go" in rendered


def test_voice_store_roundtrip():
    store = InMemoryVoiceProfileStore()
    assert store.get("u1") is None
    store.save("u1", {"tone": "dry"})
    assert store.get("u1") == {"tone": "dry"}


def test_asset_log_summarize():
    log = InMemoryAssetLog()
    assert log.summarize("u1") == ""
    log.add(MarketingAsset(user_id="u1", asset_type="email_promo", metrics={"opens": 42}))
    log.add(MarketingAsset(user_id="u1", asset_type="landing_page", marketing_angle="speed"))
    summary = log.summarize("u1")
    assert "2 prior asset(s)" in summary
    assert "opens=42" in summary
    assert "angle: speed" in summary
    assert len(log.list_for("u1")) == 2
