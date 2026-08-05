"""add billing fields to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("dodo_customer_id", sa.String(), nullable=True))
    op.add_column("users", sa.Column("subscription_status", sa.String(), nullable=True))
    op.create_index("ix_users_dodo_customer_id", "users", ["dodo_customer_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_dodo_customer_id", table_name="users")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "dodo_customer_id")
