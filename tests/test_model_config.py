import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import init_db, make_engine, make_session_factory
from app.db.model_config_store import SqlModelConfigStore
from app.llm.anthropic_client import AnthropicLLM
from app.llm.fake import FakeLLM
from app.llm.fallback import FallbackLLM
from app.llm.openrouter_client import OpenRouterLLM
from app.llm.resolver import ModelResolver
from app.main import create_app
from app.services.model_config import InMemoryModelConfigStore
from tests.conftest import TEST_JWT_SECRET, auth_header

ADMIN_EMAIL = "vipaymanshalaby@gmail.com"


# --- store ---

def test_inmemory_store_set_get_clear():
    store = InMemoryModelConfigStore()
    assert store.get_overrides() == {}
    store.set_overrides({"architect": "x/y", "writer": "", "voice": None})
    assert store.get_overrides() == {"architect": "x/y"}
    store.set_overrides({"architect": None})  # clear
    assert store.get_overrides() == {}


def test_sql_store_roundtrip(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/cfg.db")
    init_db(engine)
    store = SqlModelConfigStore(make_session_factory(engine))
    assert store.get_overrides() == {}
    store.set_overrides({"architect": "openai/gpt-4o", "voice": "google/gemini"})
    assert store.get_overrides() == {"architect": "openai/gpt-4o", "voice": "google/gemini"}
    store.set_overrides({"architect": None})
    assert store.get_overrides() == {"voice": "google/gemini"}


# --- resolver ---

def test_resolver_offline_returns_fake():
    r = ModelResolver(Settings(use_fake_llm=True), InMemoryModelConfigStore())
    assert isinstance(r.client_for("architect"), FakeLLM)


def test_resolver_default_is_anthropic_without_override():
    settings = Settings(anthropic_api_key="sk-test", use_fake_llm=False)
    r = ModelResolver(settings, InMemoryModelConfigStore())
    assert isinstance(r.client_for("writer"), AnthropicLLM)


def test_resolver_uses_openrouter_with_fallback_when_override_set():
    settings = Settings(
        anthropic_api_key="sk-test", openrouter_api_key="or-test", use_fake_llm=False
    )
    store = InMemoryModelConfigStore({"architect": "openai/gpt-4o"})
    r = ModelResolver(settings, store)
    client = r.client_for("architect")
    assert isinstance(client, FallbackLLM)
    assert isinstance(client._primary, OpenRouterLLM)
    assert isinstance(client._fallback, AnthropicLLM)
    # A role without an override still uses the default.
    assert isinstance(r.client_for("voice"), AnthropicLLM)


# --- fallback ---

class _Boom:
    def invoke(self, system, messages):
        raise RuntimeError("primary down")

    def stream(self, system, messages):
        raise RuntimeError("primary down")
        yield ""  # pragma: no cover — makes this a generator


def test_fallback_invoke_uses_fallback_on_error():
    fb = FallbackLLM(_Boom(), FakeLLM(responder=lambda s, m: "RECOVERED"))
    assert fb.invoke("sys", [{"role": "user", "content": "hi"}]) == "RECOVERED"


def test_fallback_stream_uses_fallback_on_pretoken_error():
    fb = FallbackLLM(_Boom(), FakeLLM(responder=lambda s, m: "RECOVERED"))
    out = "".join(fb.stream("sys", [{"role": "user", "content": "hi"}]))
    assert out == "RECOVERED"


# --- admin endpoints ---

@pytest.fixture
def client():
    return TestClient(create_app(Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET)))


def test_admin_models_requires_admin(client):
    # Authenticated but non-admin -> 403.
    r = client.get("/admin/models", headers=auth_header("u1", email="someone@else.com"))
    assert r.status_code == 403
    # Unauthenticated -> 401.
    assert client.get("/admin/models").status_code == 401


def test_admin_can_get_and_set_model_config(client):
    h = auth_header("admin", email=ADMIN_EMAIL)
    assert client.get("/admin/models", headers=h).json() == {
        "architect": None, "writer": None, "voice": None
    }
    r = client.put("/admin/models", json={"architect": "openai/gpt-4o", "voice": "x/y"}, headers=h)
    assert r.status_code == 200
    assert r.json() == {"architect": "openai/gpt-4o", "writer": None, "voice": "x/y"}
    # Persists on a subsequent GET.
    assert client.get("/admin/models", headers=h).json()["architect"] == "openai/gpt-4o"
