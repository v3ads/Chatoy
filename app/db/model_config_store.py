from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db.models import AppSettingRow
from app.services.model_config import (
    ROLES,
    InMemoryModelConfigStore,
    ModelConfigStore,
    normalize_overrides,
)

_PREFIX = "model_override:"


class SqlModelConfigStore:
    """Persists the admin's per-role model overrides in the app_settings table."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def get_overrides(self) -> dict[str, str]:
        with self._sf() as session:
            rows = session.scalars(select(AppSettingRow)).all()
        raw = {
            row.key[len(_PREFIX) :]: row.value
            for row in rows
            if row.key.startswith(_PREFIX) and row.value
        }
        return normalize_overrides(raw)

    def set_overrides(self, overrides: dict[str, str | None]) -> None:
        with self._sf() as session:
            for role in ROLES:
                if role not in overrides:
                    continue
                key = _PREFIX + role
                value = overrides[role]
                if value and str(value).strip():
                    session.merge(AppSettingRow(key=key, value=str(value).strip()))
                else:
                    row = session.get(AppSettingRow, key)
                    if row is not None:
                        session.delete(row)
            session.commit()


def build_model_config_store(settings: Settings) -> ModelConfigStore:
    if not settings.use_database:
        return InMemoryModelConfigStore()

    from app.db.base import make_engine, make_session_factory

    engine = make_engine(settings.database_url)  # type: ignore[arg-type]
    return SqlModelConfigStore(make_session_factory(engine))
