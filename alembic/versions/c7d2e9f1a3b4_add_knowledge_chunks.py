"""add pgvector knowledge_chunks table (semantic RAG)

Revision ID: c7d2e9f1a3b4
Revises: b2f1a0c3add1
Create Date: 2026-05-23

Postgres-only (uses the pgvector extension). The SQLite test path does not run
migrations and does not register this table on the ORM metadata.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c7d2e9f1a3b4"
down_revision: Union[str, None] = "b2f1a0c3add1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            asset_type TEXT,
            embedding vector(1536)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
