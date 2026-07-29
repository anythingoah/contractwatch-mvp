"""
Background monitoring via APScheduler. Simplest reliable option for MVP
volume (see blueprint) — swap for Celery + Redis beat once endpoint count
makes a single-process scheduler a bottleneck. Kept isolated in this module
so that swap doesn't touch monitors/diff_engine/alerts at all.

IMPORTANT: this is a single-process, in-memory scheduler. If you run more
than one API replica with RUN_SCHEDULER_IN_APP=true on each, every replica
ticks independently and checks fire once per replica. Either keep exactly
one replica running the embedded scheduler, or split it into the standalone
`worker.py` process and disable it everywhere else (RUN_SCHEDULER_IN_APP=false).

`is_due` and `run_due_checks` are separated from `_tick`/APScheduler
wiring specifically so they're testable without spinning up a real
scheduler thread — see tests/test_scheduler.py.
"""
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.metrics import scheduler_jobs_executed_total, monitor_check_failed_total
from app.models import Monitor
from app.monitors.service import run_check

logger = logging.getLogger("contractwatch.scheduler")

FREQUENCY_MINUTES = {
    "daily": 24 * 60,
    "hourly": 60,
    "every_15_min": 15,
}

scheduler = BackgroundScheduler()


def _to_utc(dt: datetime) -> datetime:
    """SQLite stores naive datetimes; normalize so subtraction never mixes aware/naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_due(monitor: Monitor, now: datetime) -> bool:
    """A monitor is due if it's never been checked, or its interval has elapsed."""
    if monitor.last_checked is None:
        return True
    interval = timedelta(minutes=FREQUENCY_MINUTES.get(monitor.frequency, 24 * 60))
    last_checked_utc = _to_utc(monitor.last_checked)
    now_utc = _to_utc(now)
    return (now_utc - last_checked_utc) >= interval


def run_due_checks(db: Session, now: datetime | None = None) -> list[int]:
    """
    Runs `run_check` for every active, due monitor. Returns the list of
    monitor IDs that were checked — mainly useful for tests/observability.
    A retry-on-failure is implicit: a failed fetch just sets status to
    'unreachable' and gets retried on the next tick automatically.
    """
    now = now or datetime.now(timezone.utc)
    monitors = db.query(Monitor).filter(Monitor.is_active == True).all()  # noqa: E712

    checked = []
    for monitor in monitors:
        if not is_due(monitor, now):
            continue
        try:
            run_check(db, monitor)
            scheduler_jobs_executed_total.inc()
            if monitor.status.value == "unreachable":
                monitor_check_failed_total.labels(reason="unreachable").inc()
            checked.append(monitor.id)
        except Exception:
            monitor_check_failed_total.labels(reason="exception").inc()
            logger.exception("Check failed", extra={"cw_monitor_id": monitor.id})
    return checked


def _tick():
    """APScheduler entrypoint — owns its own DB session lifecycle."""
    db = SessionLocal()
    try:
        run_due_checks(db)
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(_tick, IntervalTrigger(minutes=1), id="monitor_tick", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — ticking every 1 minute")


def stop_scheduler():
    # wait=True: let any in-progress check finish (and close its DB session
    # cleanly) instead of abandoning it mid-request when the container stops.
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped — in-progress checks completed")
