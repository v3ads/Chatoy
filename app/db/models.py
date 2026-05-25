from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Integer, String, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# JSONB on Postgres (indexable), plain JSON elsewhere (e.g. SQLite in tests).
JSONType = JSON().with_variant(JSONB, "postgresql")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VoiceProfileRow(Base):
    __tablename__ = "voice_profiles"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    profile: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    updated_at: Mapped[str] = mapped_column(String(40), default=_now_iso, onupdate=_now_iso)


class ProjectRow(Base):
    """A per-user workspace. Holds the evolving business + voice profile; assets
    and conversations reference it by id."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled project")
    business_profile: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    voice_profile: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), index=True, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(String(40), default=_now_iso, onupdate=_now_iso)


class MarketingAssetRow(Base):
    __tablename__ = "marketing_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    marketing_angle: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    metrics: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), index=True, default=_now_iso)


class SessionRow(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    state: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    updated_at: Mapped[str] = mapped_column(String(40), default=_now_iso, onupdate=_now_iso)


class CreditProfileRow(Base):
    __tablename__ = "credit_profiles"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    credits_balance: Mapped[float] = mapped_column(Float, default=10.0)  # Initial free credits
    auto_recharge_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[str] = mapped_column(String(40), default=_now_iso, onupdate=_now_iso)


class AppSettingRow(Base):
    """Global key/value settings (e.g. the admin's per-role model overrides)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(String(40), default=_now_iso, onupdate=_now_iso)
