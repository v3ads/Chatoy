from __future__ import annotations

from app.config import Settings
from app.services.memory import AssetLog, InMemoryAssetLog
from app.services.voice_profile import InMemoryVoiceProfileStore, VoiceProfileStore
from app.session import InMemorySessionStore, SessionStore


def build_stores(
    settings: Settings,
) -> tuple[VoiceProfileStore, AssetLog, SessionStore]:
    """Return (voice_store, asset_log, session_store) for the configured backend.

    Uses Postgres (or any SQLAlchemy URL) when ``database_url`` is set, else the
    in-memory stores. The three stores share one engine / connection pool.
    """
    if not settings.use_database:
        return InMemoryVoiceProfileStore(), InMemoryAssetLog(), InMemorySessionStore()

    from app.db.base import make_engine, make_session_factory
    from app.db.stores import SqlAssetLog, SqlSessionStore, SqlVoiceProfileStore

    engine = make_engine(settings.database_url)  # type: ignore[arg-type]
    sf = make_session_factory(engine)
    return SqlVoiceProfileStore(sf), SqlAssetLog(sf), SqlSessionStore(sf)
