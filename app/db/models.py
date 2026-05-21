from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Integer, String, Text
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


class MarketingAssetRow(Base):
    __tablename__ = "marketing_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
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
