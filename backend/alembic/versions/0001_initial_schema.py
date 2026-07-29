"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

monitor_type = sa.Enum("rest", "mcp", name="monitortype")
frequency = sa.Enum("daily", "hourly", "every_15_min", name="frequency")
monitor_status = sa.Enum("healthy", "breaking_change", "unreachable", "pending", name="monitorstatus")
severity = sa.Enum("critical", "warning", "info", name="severity")
channel_type = sa.Enum("slack", "email", "webhook", name="channeltype")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("plan", sa.String, nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "monitors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("type", monitor_type, nullable=False),
        sa.Column("api_url", sa.String, nullable=True),
        sa.Column("openapi_spec_url", sa.String, nullable=True),
        sa.Column("mcp_server_url", sa.String, nullable=True),
        sa.Column("mcp_transport", sa.String, nullable=True),
        sa.Column("frequency", frequency, nullable=False, server_default="daily"),
        sa.Column("status", monitor_status, nullable=False, server_default="pending"),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_monitors_user_id", "monitors", ["user_id"])
    # Composite index matching the scheduler's actual query pattern
    # (WHERE is_active = true, ordered/filtered by frequency + last_checked).
    op.create_index("ix_monitors_active_frequency", "monitors", ["is_active", "frequency"])

    op.create_table(
        "snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("monitor_id", sa.Integer, sa.ForeignKey("monitors.id"), nullable=False),
        sa.Column("contract", sa.JSON, nullable=False),
        sa.Column("hash", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_snapshots_monitor_id", "snapshots", ["monitor_id"])
    op.create_index("ix_snapshots_hash", "snapshots", ["hash"])
    # Snapshot history browsing is always "latest N for this monitor" —
    # a composite index on (monitor_id, created_at) serves that directly.
    op.create_index("ix_snapshots_monitor_created", "snapshots", ["monitor_id", "created_at"])

    op.create_table(
        "changes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("monitor_id", sa.Integer, sa.ForeignKey("monitors.id"), nullable=False),
        sa.Column("change_type", sa.String, nullable=False),
        sa.Column("severity", severity, nullable=False),
        sa.Column("summary", sa.String, nullable=False),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("acknowledged", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_changes_monitor_id", "changes", ["monitor_id"])
    op.create_index("ix_changes_created_at", "changes", ["created_at"])
    op.create_index("ix_changes_monitor_created", "changes", ["monitor_id", "created_at"])
    # Dashboard/alerting often filters "unacknowledged criticals" — composite
    # index serves that without a full table scan as history grows.
    op.create_index("ix_changes_monitor_severity_ack", "changes", ["monitor_id", "severity", "acknowledged"])

    op.create_table(
        "alert_channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("monitor_id", sa.Integer, sa.ForeignKey("monitors.id"), nullable=False),
        sa.Column("type", channel_type, nullable=False),
        sa.Column("configuration", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alert_channels_monitor_id", "alert_channels", ["monitor_id"])


def downgrade() -> None:
    op.drop_table("alert_channels")
    op.drop_table("changes")
    op.drop_table("snapshots")
    op.drop_table("monitors")
    op.drop_table("users")
    severity.drop(op.get_bind(), checkfirst=True)
    channel_type.drop(op.get_bind(), checkfirst=True)
    monitor_status.drop(op.get_bind(), checkfirst=True)
    frequency.drop(op.get_bind(), checkfirst=True)
    monitor_type.drop(op.get_bind(), checkfirst=True)
