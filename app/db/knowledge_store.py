from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.services.embeddings import build_embedder
from app.services.knowledge import (
    InMemoryKnowledgeStore,
    KnowledgeChunk,
    SemanticFrameworkRetriever,
)
from app.services.rag import FrameworkRetriever, InMemoryFrameworkRetriever


def _vec_literal(embedding: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


class PgVectorKnowledgeStore:
    """Knowledge store backed by Postgres + pgvector (raw SQL, no ORM column so
    the SQLite test path is unaffected)."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def upsert(self, items: list[tuple[KnowledgeChunk, list[float]]]) -> None:
        with self._sf() as session:
            for chunk, emb in items:
                session.execute(
                    text(
                        "INSERT INTO knowledge_chunks (id, content, asset_type, embedding) "
                        "VALUES (:id, :content, :asset_type, (:emb)::vector) "
                        "ON CONFLICT (id) DO UPDATE SET "
                        "content = EXCLUDED.content, asset_type = EXCLUDED.asset_type, "
                        "embedding = EXCLUDED.embedding"
                    ),
                    {
                        "id": chunk.id,
                        "content": chunk.content,
                        "asset_type": chunk.asset_type,
                        "emb": _vec_literal(emb),
                    },
                )
            session.commit()

    def search(self, embedding: list[float], k: int, asset_type: str | None = None) -> list[str]:
        params = {"q": _vec_literal(embedding), "k": k}
        order = "embedding <=> (:q)::vector"
        if asset_type:
            params["at"] = asset_type
            # Soft boost (smaller distance = closer) for the matching asset type.
            order = "(embedding <=> (:q)::vector) - (CASE WHEN asset_type = :at THEN 0.05 ELSE 0 END)"
        with self._sf() as session:
            rows = session.execute(
                text(f"SELECT content FROM knowledge_chunks ORDER BY {order} ASC LIMIT :k"),
                params,
            ).all()
        return [r[0] for r in rows]

    def count(self) -> int:
        with self._sf() as session:
            return int(session.execute(text("SELECT COUNT(*) FROM knowledge_chunks")).scalar() or 0)


def build_knowledge_retriever(settings: Settings) -> FrameworkRetriever:
    """Semantic (pgvector) retriever when embeddings + DB are configured;
    otherwise the built-in keyword framework library."""
    keyword = InMemoryFrameworkRetriever()
    embedder = build_embedder(settings)
    if embedder is None:
        return keyword

    # Only use pgvector with a real (OpenAI) embedder + a database; the offline
    # fake embedder uses a tiny dim that won't match the vector(1536) column.
    if settings.openai_api_key and settings.use_database:
        from app.db.engine import shared_engine

        sf = sessionmaker(bind=shared_engine(settings.database_url), expire_on_commit=False, future=True)  # type: ignore[arg-type]
        store = PgVectorKnowledgeStore(sf)
    else:
        store = InMemoryKnowledgeStore()

    return SemanticFrameworkRetriever(embedder, store, keyword)
