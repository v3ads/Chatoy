from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Protocol

from app.services.embeddings import Embedder
from app.services.rag import FrameworkRetriever


@dataclass
class KnowledgeChunk:
    content: str
    asset_type: str = "general"
    tags: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:32]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


class KnowledgeStore(Protocol):
    def upsert(self, items: list[tuple[KnowledgeChunk, list[float]]]) -> None: ...

    def search(self, embedding: list[float], k: int, asset_type: str | None = None) -> list[str]: ...

    def count(self) -> int: ...


class InMemoryKnowledgeStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[KnowledgeChunk, list[float]]] = {}

    def upsert(self, items: list[tuple[KnowledgeChunk, list[float]]]) -> None:
        for chunk, emb in items:
            self._items[chunk.id] = (chunk, emb)

    def search(self, embedding: list[float], k: int, asset_type: str | None = None) -> list[str]:
        scored = []
        for chunk, emb in self._items.values():
            score = _cosine(embedding, emb)
            if asset_type and chunk.asset_type == asset_type:
                score += 0.05  # light boost for the matching asset type
            scored.append((score, chunk.content))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [content for _, content in scored[:k]]

    def count(self) -> int:
        return len(self._items)


class SemanticFrameworkRetriever:
    """Vector-search retriever over the knowledge base, with the built-in
    keyword framework library as a fallback when the store is empty or a search
    fails. Implements ``retrieve`` (for compatibility) and ``search``."""

    def __init__(
        self,
        embedder: Embedder,
        store: KnowledgeStore,
        fallback: FrameworkRetriever,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._fallback = fallback

    def seed(self, chunks: list[KnowledgeChunk]) -> int:
        embeddings = self._embedder.embed([c.content for c in chunks])
        if len(embeddings) != len(chunks):
            raise RuntimeError(
                f"embedder returned {len(embeddings)} vectors for {len(chunks)} chunks"
            )
        self._store.upsert(list(zip(chunks, embeddings)))
        return self._store.count()

    def count(self) -> int:
        return self._store.count()

    @property
    def backend(self) -> str:
        """Storage backend name — distinguishes a persistent pgvector store from
        the ephemeral in-memory one (which silently loses data across restarts/
        workers)."""
        return type(self._store).__name__

    def search(self, query: str, k: int = 3, asset_type: str | None = None) -> list[str]:
        try:
            if self._store.count() > 0:
                emb = self._embedder.embed_one(query)
                hits = self._store.search(emb, k, asset_type=asset_type)
                if hits:
                    return hits
        except Exception:  # noqa: BLE001 — never let retrieval break a generation
            pass
        return self._fallback.retrieve(asset_type or "", k)

    def retrieve(self, asset_type: str, k: int = 3) -> list[str]:
        return self.search(asset_type, k=k, asset_type=asset_type)
