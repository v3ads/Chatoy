from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


@lru_cache(maxsize=8)
def shared_engine(url: str) -> Engine:
    """A small, cached engine shared by the auxiliary stores (model config,
    knowledge base) so they don't each open their own connection pool."""
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=2,
        connect_args=connect_args,
    )
