from __future__ import annotations

import hashlib

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.services.embeddings import Embedder, build_embedder


def _vec_literal(embedding: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


def _mem_id(project_id: str, content: str) -> str:
    return hashlib.sha256(f"{project_id}:{content}".encode()).hexdigest()[:32]


class PgVectorProjectMemory:
    """Per-project memory of finished assets, backed by Postgres + pgvector.

    Lets the Architect semantically recall the most relevant prior work for a
    project, not just a flat list — so guidance compounds as the project grows."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def add(self, project_id: str, asset_type: str, content: str, embedding: list[float]) -> None:
        with self._sf() as session:
            session.execute(
                text(
                    "INSERT INTO project_memory (id, project_id, asset_type, content, embedding) "
                    "VALUES (:id, :pid, :at, :content, (:emb)::vector) "
                    "ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, "
                    "asset_type = EXCLUDED.asset_type, embedding = EXCLUDED.embedding"
                ),
                {
                    "id": _mem_id(project_id, content),
                    "pid": project_id,
                    "at": asset_type,
                    "content": content,
                    "emb": _vec_literal(embedding),
                },
            )
            session.commit()

    def search(self, project_id: str, embedding: list[float], k: int) -> list[str]:
        with self._sf() as session:
            rows = session.execute(
                text(
                    "SELECT content FROM project_memory WHERE project_id = :pid "
                    "ORDER BY embedding <=> (:q)::vector ASC LIMIT :k"
                ),
                {"pid": project_id, "q": _vec_literal(embedding), "k": k},
            ).all()
        return [r[0] for r in rows]


class ProjectRecall:
    """Embeds finished assets into per-project memory and recalls relevant ones.

    Every method is best-effort: a failure (bad embeddings key, DB hiccup) is
    swallowed so it can never break a generation — recall simply returns []."""

    def __init__(self, embedder: Embedder, store: PgVectorProjectMemory) -> None:
        self._embedder = embedder
        self._store = store

    def remember(self, project_id: str, asset_type: str, content: str) -> None:
        if not (project_id and content.strip()):
            return
        try:
            emb = self._embedder.embed_one(content)
            self._store.add(project_id, asset_type, content, emb)
        except Exception:  # noqa: BLE001 — memory writes must never break a turn
            pass

    def recall(self, project_id: str, query: str, k: int = 3) -> list[str]:
        if not (project_id and query.strip()):
            return []
        try:
            emb = self._embedder.embed_one(query)
            return self._store.search(project_id, emb, k)
        except Exception:  # noqa: BLE001
            return []


def build_project_recall(settings: Settings) -> ProjectRecall | None:
    """A pgvector-backed recall when embeddings + a database are configured;
    otherwise None (the Architect falls back to the flat asset digest)."""
    embedder = build_embedder(settings)
    if embedder is None or not (settings.openai_api_key and settings.use_database):
        return None
    from app.db.engine import shared_engine

    sf = sessionmaker(
        bind=shared_engine(settings.database_url),  # type: ignore[arg-type]
        expire_on_commit=False,
        future=True,
    )
    return ProjectRecall(embedder, PgVectorProjectMemory(sf))
