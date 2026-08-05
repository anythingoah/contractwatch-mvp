"""
All SQLAlchemy models in one file — deliberately, per the "no unnecessary
abstraction" rule. This is a small schema; splitting it across files would
just add import indirection for no benefit at this size.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, Enum, Index
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class MonitorType(str, enum.Enum):
    rest = "rest"
    mcp = "mcp"


class Frequency(str, enum.Enum):
    daily = "daily"
    hourly = "hourly"
    every_15_min = "every_15_min"


class MonitorStatus(str, enum.Enum):
    healthy = "healthy"
    breaking_change = "breaking_change"
    unreachable = "unreachable"
    pending = "pending"  # no successful check yet


class Severity(str, enum.Enum):
    critical = "critical"   # breaking
    warning = "warning"     # potentially breaking / medium
    info = "info"           # informational / low


class ChannelType(str, enum.Enum):
    slack = "slack"
    email = "email"
    webhook = "webhook"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan = Column(String, default="free", nullable=False)  # free | developer | team
    dodo_customer_id = Column(String, nullable=True, unique=True, index=True)
    subscription_status = Column(String, nullable=True)  # active | past_due | canceled | failed | None
    created_at = Column(DateTime(timezone=True), default=utcnow)

    monitors = relationship("Monitor", back_populates="owner", cascade="all, delete-orphan")


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(MonitorType), nullable=False)

    # REST fields
    api_url = Column(String, nullable=True)
    openapi_spec_url = Column(String, nullable=True)

    # MCP fields
    mcp_server_url = Column(String, nullable=True)
    mcp_transport = Column(String, nullable=True)  # "http" | "sse"

    frequency = Column(Enum(Frequency), default=Frequency.daily, nullable=False)
    status = Column(Enum(MonitorStatus), default=MonitorStatus.pending, nullable=False)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    owner = relationship("User", back_populates="monitors")
    snapshots = relationship("Snapshot", back_populates="monitor", cascade="all, delete-orphan")
    changes = relationship("Change", back_populates="monitor", cascade="all, delete-orphan")
    channels = relationship("AlertChannel", back_populates="monitor", cascade="all, delete-orphan")

    # Matches the scheduler's actual query: WHERE is_active = true, checked
    # against frequency + last_checked every tick.
    __table_args__ = (Index("ix_monitors_active_frequency", "is_active", "frequency"),)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)
    contract = Column(JSON, nullable=False)   # normalized contract JSON
    hash = Column(String, nullable=False, index=True)  # sha256 of normalized contract
    created_at = Column(DateTime(timezone=True), default=utcnow)

    monitor = relationship("Monitor", back_populates="snapshots")

    # History browsing is always "latest N for this monitor" — serve that
    # with one composite index instead of a monitor_id scan + sort.
    __table_args__ = (Index("ix_snapshots_monitor_created", "monitor_id", "created_at"),)


class Change(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)
    change_type = Column(String, nullable=False)   # e.g. "removed_parameter"
    severity = Column(Enum(Severity), nullable=False)
    summary = Column(String, nullable=False)
    details = Column(JSON, nullable=True)   # {old_value, new_value, path, ai_explanation?}
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    monitor = relationship("Monitor", back_populates="changes")

    __table_args__ = (
        Index("ix_changes_monitor_created", "monitor_id", "created_at"),
        # Dashboards/alert logic often filter "unacknowledged criticals for
        # this monitor" — composite index serves that without a full scan.
        Index("ix_changes_monitor_severity_ack", "monitor_id", "severity", "acknowledged"),
    )


class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False, index=True)
    type = Column(Enum(ChannelType), nullable=False)
    configuration = Column(JSON, nullable=False)  # {"webhook_url": ...} / {"email": ...} / {"url": ...}
    created_at = Column(DateTime(timezone=True), default=utcnow)

    monitor = relationship("Monitor", back_populates="channels")
