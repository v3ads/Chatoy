"""add projects, project_id on assets, and per-project pgvector memory

Revision ID: a3c1f0d2e4b5
Revises: c7d2e9f1a3b4
Create Date: 2026-05-25

Additive only: creates the projects table, adds a nullable project_id to
marketing_assets, and creates the Postgres-only project_memory table (pgvector).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a3c1f0d2e4b5"
down_revision: Union[str, None] = "c7d2e9f1a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("business_profile", postgresql.JSONB(), nullable=False),
        sa.Column("voice_profile", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])

    op.add_column(
        "marketing_assets",
        sa.Column("project_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_marketing_assets_project_id", "marketing_assets", ["project_id"])

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_memory (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            asset_type TEXT,
            content TEXT NOT NULL,
            embedding vector(1536),
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_memory_project_id ON project_memory (project_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS project_memory")
    op.drop_index("ix_marketing_assets_project_id", table_name="marketing_assets")
    op.drop_column("marketing_assets", "project_id")
    op.drop_index("ix_projects_created_at", table_name="projects")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")
