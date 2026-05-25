from __future__ import annotations

import hashlib
import re
import struct
from typing import Protocol

import httpx

from app.config import Settings


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]: ...


class OpenAIEmbedder:
    """Embeddings via OpenAI's REST API (httpx; no SDK dependency)."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dim: int = 1536,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
    ) -> None:
        self.dim = dim
        self._model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.post(
            "/embeddings", json={"model": self._model, "input": texts}
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class FakeEmbedder:
    """Deterministic, offline embeddings for tests/local dev.

    Hashes tokens into a fixed-dim bag-of-words vector so semantically similar
    strings (shared words) land near each other under cosine similarity.
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            h = hashlib.md5(token.encode()).digest()
            idx = struct.unpack("<I", h[:4])[0] % self.dim
            v[idx] += 1.0
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / norm for x in v]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._vec(text)


def build_embedder(settings: Settings) -> Embedder | None:
    """OpenAI embedder when configured, the offline fake when forced, else None
    (caller should fall back to keyword retrieval)."""
    if settings.use_fake_llm:
        return FakeEmbedder()
    if settings.openai_api_key:
        return OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            dim=settings.embedding_dim,
            base_url=settings.openai_base_url,
        )
    return None
