"""initial schema: voice_profiles, marketing_assets, sessions

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# JSONB on Postgres, plain JSON elsewhere — mirrors app.db.models.JSONType.
JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    op.create_table(
        "voice_profiles",
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("profile", JSONType, nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "marketing_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("marketing_angle", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metrics", JSONType, nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_marketing_assets_user_id", "marketing_assets", ["user_id"]
    )
    op.create_index(
        "ix_marketing_assets_created_at", "marketing_assets", ["created_at"]
    )
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("state", JSONType, nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("session_id"),
    )


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_index("ix_marketing_assets_created_at", table_name="marketing_assets")
    op.drop_index("ix_marketing_assets_user_id", table_name="marketing_assets")
    op.drop_table("marketing_assets")
    op.drop_table("voice_profiles")
