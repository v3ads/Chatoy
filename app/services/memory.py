from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass
class MarketingAsset:
    """A completed asset plus whatever performance the user reported.

    Powers the "Stacking Wins" loop: the Architect reads the history of past
    assets and metrics (scoped to the active project) to decide the next
    highest-leverage move.
    """

    user_id: str
    asset_type: str
    project_id: str = ""
    marketing_angle: str = ""
    content: str = ""
    metrics: dict = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    id: int | None = None


def summarize_assets(assets: list[MarketingAsset]) -> str:
    """A compact, model-readable digest of past assets and their results.

    Shared by every AssetLog implementation so the Architect sees identical
    context regardless of backing store.
    """
    if not assets:
        return ""
    lines = [f"{len(assets)} prior asset(s):"]
    for a in assets:
        metrics = (
            ", ".join(f"{k}={v}" for k, v in a.metrics.items())
            if a.metrics
            else "no metrics reported"
        )
        angle = f" — angle: {a.marketing_angle}" if a.marketing_angle else ""
        lines.append(f"- {a.asset_type}{angle} ({metrics})")
    return "\n".join(lines)


class AssetLog(Protocol):
    def add(self, asset: MarketingAsset) -> MarketingAsset: ...

    def list_for(self, project_id: str) -> list[MarketingAsset]: ...

    def summarize(self, project_id: str) -> str: ...

    def update_metrics(
        self, asset_id: int, metrics: dict, *, project_id: str | None = None
    ) -> MarketingAsset | None: ...


class InMemoryAssetLog:
    """Default asset log. Swap for a ``marketing_assets`` table in production."""

    def __init__(self) -> None:
        self._by_project: dict[str, list[MarketingAsset]] = {}
        self._seq = 0

    def add(self, asset: MarketingAsset) -> MarketingAsset:
        self._seq += 1
        asset.id = self._seq
        self._by_project.setdefault(asset.project_id, []).append(asset)
        return asset

    def list_for(self, project_id: str) -> list[MarketingAsset]:
        return list(self._by_project.get(project_id, []))

    def summarize(self, project_id: str) -> str:
        return summarize_assets(self._by_project.get(project_id, []))

    def update_metrics(
        self, asset_id: int, metrics: dict, *, project_id: str | None = None
    ) -> MarketingAsset | None:
        for assets in self._by_project.values():
            for a in assets:
                if a.id == asset_id and (project_id is None or a.project_id == project_id):
                    a.metrics = {**(a.metrics or {}), **(metrics or {})}
                    return a
        return None
