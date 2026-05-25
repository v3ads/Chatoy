from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_project_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Project:
    """A workspace that holds everything the agents learn about one business:
    its evolving profile, voice, assets and conversation. Switching projects
    swaps the entire intelligence context."""

    user_id: str
    name: str
    id: str = field(default_factory=new_project_id)
    business_profile: dict = field(default_factory=dict)
    voice_profile: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


def merge_profile(base: dict | None, incoming: dict | None) -> dict:
    """Non-destructively fold newly learned facts into the stored profile.

    New keys are added; existing keys are overwritten only when the incoming
    value is non-empty, so a vague later answer never wipes a concrete fact."""
    merged = dict(base or {})
    for key, value in (incoming or {}).items():
        if value in (None, "", [], {}):
            continue
        merged[key] = value
    return merged


class ProjectStore(Protocol):
    def create(self, user_id: str, name: str) -> Project: ...

    def get(self, project_id: str) -> Project | None: ...

    def list_for(self, user_id: str) -> list[Project]: ...

    def update(
        self,
        project_id: str,
        *,
        name: str | None = None,
        business_profile: dict | None = None,
        voice_profile: dict | None = None,
    ) -> Project | None: ...

    def delete(self, project_id: str) -> None: ...

    def ensure_default(self, user_id: str) -> Project: ...


class InMemoryProjectStore:
    """Default store. Swap for the SQL-backed store via the database config."""

    def __init__(self) -> None:
        self._by_id: dict[str, Project] = {}

    def create(self, user_id: str, name: str) -> Project:
        project = Project(user_id=user_id, name=name or "Untitled project")
        self._by_id[project.id] = project
        return project

    def get(self, project_id: str) -> Project | None:
        return self._by_id.get(project_id)

    def list_for(self, user_id: str) -> list[Project]:
        return sorted(
            (p for p in self._by_id.values() if p.user_id == user_id),
            key=lambda p: p.created_at,
        )

    def update(
        self,
        project_id: str,
        *,
        name: str | None = None,
        business_profile: dict | None = None,
        voice_profile: dict | None = None,
    ) -> Project | None:
        project = self._by_id.get(project_id)
        if project is None:
            return None
        if name is not None:
            project.name = name
        if business_profile is not None:
            project.business_profile = business_profile
        if voice_profile is not None:
            project.voice_profile = voice_profile
        project.updated_at = _now_iso()
        return project

    def delete(self, project_id: str) -> None:
        self._by_id.pop(project_id, None)

    def ensure_default(self, user_id: str) -> Project:
        existing = self.list_for(user_id)
        return existing[0] if existing else self.create(user_id, "My First Project")
