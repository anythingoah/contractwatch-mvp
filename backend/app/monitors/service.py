"""
Core monitor business logic: CRUD, plan-limit enforcement, and the check
pipeline (fetch -> normalize -> hash -> diff -> classify -> alert).
This is the module that ties fetchers + diff_engine + alerts together.
"""
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import (
    Monitor, Snapshot, Change, AlertChannel, User,
    MonitorType, MonitorStatus, Severity, ChannelType,
)
from app.core.config import settings
from app.monitors.schemas import MonitorCreate
from app.fetchers.rest_fetcher import fetch_openapi_spec, FetchError
from app.fetchers.mcp_fetcher import fetch_mcp_tools
from app.diff_engine.normalize import normalize_openapi, normalize_mcp
from app.diff_engine.engine import diff_contracts, contract_hash, overall_severity, is_breaking
from app.alerts.service import dispatch_alerts
from app.alerts.ai_explain import explain_breaking_change

logger = logging.getLogger("contractwatch.monitors")

PLAN_LIMITS = {
    "free": {"monitor_limit": settings.free_plan_monitor_limit, "frequencies": {"daily"}},
    "developer": {"monitor_limit": 20, "frequencies": {"daily", "hourly"}},
    "team": {"monitor_limit": None, "frequencies": {"daily", "hourly", "every_15_min"}},
}


def _enforce_plan_limits(db: Session, user: User, frequency: str) -> None:
    limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])

    if limits["monitor_limit"] is not None:
        count = db.query(Monitor).filter(Monitor.user_id == user.id).count()
        if count >= limits["monitor_limit"]:
            raise HTTPException(
                status.HTTP_402_PAYMENT_REQUIRED,
                f"Your plan allows up to {limits['monitor_limit']} monitors. Upgrade to add more.",
            )

    if frequency not in limits["frequencies"]:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Your plan doesn't include '{frequency}' checks. Upgrade to unlock this frequency.",
        )


def create_monitor(db: Session, user: User, payload: MonitorCreate) -> Monitor:
    _enforce_plan_limits(db, user, payload.frequency)

    monitor = Monitor(
        user_id=user.id,
        name=payload.name,
        type=MonitorType(payload.type),
        api_url=payload.api_url,
        openapi_spec_url=payload.openapi_spec_url,
        mcp_server_url=payload.mcp_server_url,
        mcp_transport=payload.mcp_transport,
        frequency=payload.frequency,
    )
    db.add(monitor)
    try:
        db.flush()  # get monitor.id before adding channels

        for ch in payload.channels:
            db.add(AlertChannel(monitor_id=monitor.id, type=ChannelType(ch.type), configuration=ch.configuration))

        db.commit()
        db.refresh(monitor)
    except Exception:
        db.rollback()
        raise
    return monitor


def list_monitors(db: Session, user: User, limit: int, offset: int) -> list[tuple[Monitor, int, int]]:
    """
    Returns monitors with change counts and snapshot counts, one query, no N+1.

    Uses correlated scalar subqueries rather than two outerjoins — joining
    Monitor to both Change and Snapshot directly would multiply rows before
    GROUP BY (e.g. 3 changes x 5 snapshots = 15 rows for one monitor),
    giving wrong counts. Subqueries sidestep that entirely.
    """
    change_count_subq = (
        db.query(func.count(Change.id))
        .filter(Change.monitor_id == Monitor.id)
        .correlate(Monitor)
        .scalar_subquery()
    )
    snapshot_count_subq = (
        db.query(func.count(Snapshot.id))
        .filter(Snapshot.monitor_id == Monitor.id)
        .correlate(Monitor)
        .scalar_subquery()
    )

    rows = (
        db.query(Monitor, change_count_subq.label("change_count"), snapshot_count_subq.label("snapshot_count"))
        .filter(Monitor.user_id == user.id)
        .order_by(Monitor.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [(monitor, int(change_count), int(snapshot_count)) for monitor, change_count, snapshot_count in rows]


def get_snapshot_count(db: Session, monitor_id: int) -> int:
    """Used by the single-monitor route — see routes.py get_monitor."""
    return db.query(func.count(Snapshot.id)).filter(Snapshot.monitor_id == monitor_id).scalar() or 0


def list_recent_changes(db: Session, user: User, limit: int) -> list[tuple[Change, int, str]]:
    """
    Cross-monitor activity feed: the N most recent changes across every
    monitor this user owns, newest first. Unlike list_changes (below),
    this isn't scoped to one monitor_id — it's what powers the dashboard's
    "recent activity" view.
    """
    rows = (
        db.query(Change, Monitor.id, Monitor.name)
        .join(Monitor, Monitor.id == Change.monitor_id)
        .filter(Monitor.user_id == user.id)
        .order_by(Change.created_at.desc())
        .limit(limit)
        .all()
    )
    return [(change, monitor_id, monitor_name) for change, monitor_id, monitor_name in rows]


def get_monitor(db: Session, user: User, monitor_id: int) -> Monitor:
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id, Monitor.user_id == user.id).first()
    if not monitor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Monitor not found")
    return monitor


def delete_monitor(db: Session, user: User, monitor_id: int) -> None:
    monitor = get_monitor(db, user, monitor_id)
    try:
        db.delete(monitor)
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_changes(
    db: Session,
    user: User,
    monitor_id: int,
    limit: int | None = None,
    offset: int = 0,
) -> list[Change]:
    get_monitor(db, user, monitor_id)  # ownership check
    query = (
        db.query(Change)
        .filter(Change.monitor_id == monitor_id)
        .order_by(Change.created_at.desc())
    )
    if limit is not None:
        query = query.limit(limit).offset(offset)
    return query.all()


def run_check(db: Session, monitor: Monitor) -> dict:
    """
    The core pipeline. Returns a small result dict; used by both the manual
    "check now" endpoint and the background scheduler.
    """
    from datetime import datetime, timezone

    try:
        if monitor.type == MonitorType.rest:
            raw = fetch_openapi_spec(monitor.openapi_spec_url)
            normalized = normalize_openapi(raw)
        else:
            raw = fetch_mcp_tools(monitor.mcp_server_url, monitor.mcp_transport or "http")
            normalized = normalize_mcp(raw)
    except FetchError as e:
        monitor.status = MonitorStatus.unreachable
        monitor.last_checked = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        logger.warning(
            "Monitor unreachable", extra={"cw_monitor_id": monitor.id, "cw_error": str(e)}
        )
        return {"status": "unreachable", "changes_detected": 0, "breaking": False}

    try:
        new_hash = contract_hash(normalized)
        previous = (
            db.query(Snapshot)
            .filter(Snapshot.monitor_id == monitor.id)
            .order_by(Snapshot.created_at.desc())
            .first()
        )

        # Always store the snapshot — this is what "unlimited history" browses.
        db.add(Snapshot(monitor_id=monitor.id, contract=normalized, hash=new_hash))
        monitor.last_checked = datetime.now(timezone.utc)

        if previous is None:
            # First ever check for this monitor — nothing to diff against yet.
            monitor.status = MonitorStatus.healthy
            db.commit()
            return {"status": "baseline_created", "changes_detected": 0, "breaking": False}

        if previous.hash == new_hash:
            # No structural change — cheap path, skip diffing entirely.
            monitor.status = MonitorStatus.healthy
            db.commit()
            return {"status": "no_change", "changes_detected": 0, "breaking": False}

        changes = diff_contracts(previous.contract, normalized)
        severity = overall_severity(changes)
        breaking = is_breaking(changes)

        ai_explanation = explain_breaking_change(monitor.name, changes) if breaking else None

        for c in changes:
            details = {"old_value": c["old_value"], "new_value": c["new_value"], "path": c["path"]}
            if ai_explanation and c["severity"] == "critical":
                details["ai_explanation"] = ai_explanation
            db.add(Change(
                monitor_id=monitor.id,
                change_type=c["type"],
                severity=Severity(c["severity"]),
                summary=c["message"],
                details=details,
            ))

        monitor.status = MonitorStatus.breaking_change if breaking else MonitorStatus.healthy
        db.commit()

        logger.info(
            "Contract drift detected",
            extra={
                "cw_monitor_id": monitor.id,
                "cw_severity": severity,
                "cw_change_count": len(changes),
                "cw_breaking": breaking,
            },
        )

        dispatch_alerts(db, monitor, changes, severity)

        return {"status": "changes_detected", "changes_detected": len(changes), "breaking": breaking}
    except Exception:
        db.rollback()
        raise
