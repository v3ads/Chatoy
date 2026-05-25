import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.embeddings import FakeEmbedder
from app.services.knowledge import InMemoryKnowledgeStore, SemanticFrameworkRetriever
from app.services.knowledge_seed import SEED_CHUNKS
from app.services.rag import InMemoryFrameworkRetriever
from tests.conftest import TEST_JWT_SECRET, auth_header

ADMIN_EMAIL = "vipaymanshalaby@gmail.com"


def _retriever() -> SemanticFrameworkRetriever:
    return SemanticFrameworkRetriever(
        FakeEmbedder(), InMemoryKnowledgeStore(), InMemoryFrameworkRetriever()
    )


def test_empty_store_falls_back_to_keyword_library():
    r = _retriever()
    assert r.count() == 0
    out = r.search("email promo", k=3, asset_type="email_promo")
    # Falls back to the built-in keyword frameworks (non-empty).
    assert out and out == InMemoryFrameworkRetriever().retrieve("email_promo", 3)


def test_seed_then_semantic_search_returns_relevant_chunk():
    r = _retriever()
    n = r.seed(SEED_CHUNKS)
    assert n == len(SEED_CHUNKS) > 0

    out = r.search("BAB before after bridge email", k=3, asset_type="email_promo")
    assert len(out) == 3
    # The distinctive BAB chunk should surface for that query.
    assert any("BAB" in c for c in out)
    # Everything returned comes from the seeded corpus.
    seed_texts = {c.content for c in SEED_CHUNKS}
    assert all(c in seed_texts for c in out)


def test_retrieve_delegates_to_search():
    r = _retriever()
    r.seed(SEED_CHUNKS)
    assert len(r.retrieve("landing_page", k=2)) == 2


# --- admin seed endpoint ---

@pytest.fixture
def client():
    return TestClient(create_app(Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET)))


def test_knowledge_admin_seed_and_status(client):
    h = auth_header("admin", email=ADMIN_EMAIL)
    # Non-admin is rejected before any work.
    assert client.post("/admin/knowledge/seed", headers=auth_header("u", email="x@y.com")).status_code == 403

    status = client.get("/admin/knowledge", headers=h).json()
    assert status["count"] == 0 and status["semantic"] is True

    seeded = client.post("/admin/knowledge/seed", headers=h).json()
    assert seeded["count"] == len(SEED_CHUNKS)
    assert client.get("/admin/knowledge", headers=h).json()["count"] == len(SEED_CHUNKS)
