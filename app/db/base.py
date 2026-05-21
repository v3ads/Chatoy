from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str, echo: bool = False) -> Engine:
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # Stores open a fresh session per call, so cross-thread use is safe.
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        echo=echo,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db(engine: Engine) -> None:
    """Create tables directly from the ORM metadata.

    Convenient for SQLite / quick local dev and tests. Production should use
    the Alembic migrations instead.
    """
    from app.db import models  # noqa: F401 — register mappers

    Base.metadata.create_all(engine)
