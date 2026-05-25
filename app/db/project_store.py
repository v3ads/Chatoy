from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db.models import ProjectRow
from app.services.projects import (
    InMemoryProjectStore,
    Project,
    ProjectStore,
    new_project_id,
)


def _to_project(row: ProjectRow) -> Project:
    return Project(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        business_profile=dict(row.business_profile or {}),
        voice_profile=dict(row.voice_profile or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlProjectStore:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def create(self, user_id: str, name: str) -> Project:
        with self._sf() as session:
            row = ProjectRow(
                id=new_project_id(),
                user_id=user_id,
                name=name or "Untitled project",
                business_profile={},
                voice_profile={},
            )
            session.add(row)
            session.commit()
            return _to_project(row)

    def get(self, project_id: str) -> Project | None:
        with self._sf() as session:
            row = session.get(ProjectRow, project_id)
            return _to_project(row) if row is not None else None

    def list_for(self, user_id: str) -> list[Project]:
        with self._sf() as session:
            rows = session.scalars(
                select(ProjectRow)
                .where(ProjectRow.user_id == user_id)
                .order_by(ProjectRow.created_at)
            ).all()
            return [_to_project(r) for r in rows]

    def update(
        self,
        project_id: str,
        *,
        name: str | None = None,
        business_profile: dict | None = None,
        voice_profile: dict | None = None,
    ) -> Project | None:
        with self._sf() as session:
            row = session.get(ProjectRow, project_id)
            if row is None:
                return None
            if name is not None:
                row.name = name
            if business_profile is not None:
                row.business_profile = business_profile
            if voice_profile is not None:
                row.voice_profile = voice_profile
            session.commit()
            return _to_project(row)

    def delete(self, project_id: str) -> None:
        with self._sf() as session:
            row = session.get(ProjectRow, project_id)
            if row is not None:
                session.delete(row)
                session.commit()

    def ensure_default(self, user_id: str) -> Project:
        existing = self.list_for(user_id)
        return existing[0] if existing else self.create(user_id, "My First Project")


def build_project_store(settings: Settings) -> ProjectStore:
    if not settings.use_database:
        return InMemoryProjectStore()
    from app.db.engine import shared_engine

    sf = sessionmaker(
        bind=shared_engine(settings.database_url),  # type: ignore[arg-type]
        expire_on_commit=False,
        future=True,
    )
    return SqlProjectStore(sf)
