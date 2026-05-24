from __future__ import annotations

from typing import Protocol

# Agent roles that can be assigned an OpenRouter model by the admin.
ROLES = ("architect", "writer", "voice")


def normalize_overrides(raw: dict) -> dict[str, str]:
    """Keep only known roles with a non-empty model id."""
    out: dict[str, str] = {}
    for role in ROLES:
        value = (raw or {}).get(role)
        if isinstance(value, str) and value.strip():
            out[role] = value.strip()
    return out


class ModelConfigStore(Protocol):
    """Global, runtime-editable per-role model overrides (admin controlled)."""

    def get_overrides(self) -> dict[str, str]: ...

    def set_overrides(self, overrides: dict[str, str | None]) -> None: ...


class InMemoryModelConfigStore:
    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        self._overrides = normalize_overrides(overrides or {})

    def get_overrides(self) -> dict[str, str]:
        return dict(self._overrides)

    def set_overrides(self, overrides: dict[str, str | None]) -> None:
        for role in ROLES:
            if role not in overrides:
                continue
            value = overrides[role]
            if value and str(value).strip():
                self._overrides[role] = str(value).strip()
            else:
                self._overrides.pop(role, None)
