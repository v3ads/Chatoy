"""add stripe_customer_id to credit_profiles

Revision ID: b5d3c1e7f2a9
Revises: a3c1f0d2e4b5
Create Date: 2026-05-25

Maps a Stripe customer to a user so subscription renewals can grant credits.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b5d3c1e7f2a9"
down_revision: Union[str, None] = "a3c1f0d2e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "credit_profiles",
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_credit_profiles_stripe_customer_id",
        "credit_profiles",
        ["stripe_customer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_credit_profiles_stripe_customer_id", table_name="credit_profiles")
    op.drop_column("credit_profiles", "stripe_customer_id")
