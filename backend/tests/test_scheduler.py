"""
Scheduler behavior: which monitors are "due", and that run_due_checks only
checks the due ones, marks the rest untouched, and survives one monitor
raising an exception without skipping the others.
"""
from datetime import datetime, timezone, timedelta

from app.models import User, Monitor, MonitorType
from app.scheduler.jobs import is_due, run_due_checks

_user_counter = 0


def _make_monitor(db_session, frequency="daily", last_checked=None, is_active=True) -> Monitor:
    global _user_counter
    _user_counter += 1
    user = User(email=f"sched-{_user_counter}-{frequency}@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()
    monitor = Monitor(
        user_id=user.id, name="Sched Test", type=MonitorType.mcp,
        mcp_server_url="https://mcp.example.com", frequency=frequency,
        last_checked=last_checked, is_active=is_active,
    )
    db_session.add(monitor)
    db_session.commit()
    return monitor


def test_never_checked_monitor_is_due():
    monitor = Monitor(frequency="daily", last_checked=None)
    assert is_due(monitor, datetime.now(timezone.utc)) is True


def test_monitor_within_interval_is_not_due():
    now = datetime.now(timezone.utc)
    monitor = Monitor(frequency="daily", last_checked=now - timedelta(hours=1))
    assert is_due(monitor, now) is False


def test_monitor_past_interval_is_due():
    now = datetime.now(timezone.utc)
    monitor = Monitor(frequency="hourly", last_checked=now - timedelta(hours=2))
    assert is_due(monitor, now) is True


def test_run_due_checks_only_checks_due_monitors(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    due = _make_monitor(db_session, frequency="hourly", last_checked=now - timedelta(hours=2))
    not_due = _make_monitor(db_session, frequency="daily", last_checked=now - timedelta(minutes=5))

    checked_ids = []
    monkeypatch.setattr(
        "app.scheduler.jobs.run_check",
        lambda db, monitor: checked_ids.append(monitor.id),
    )

    result = run_due_checks(db_session, now=now)
    assert result == [due.id]
    assert not_due.id not in checked_ids


def test_run_due_checks_skips_inactive_monitors(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    _make_monitor(db_session, frequency="hourly", last_checked=now - timedelta(hours=5), is_active=False)

    monkeypatch.setattr("app.scheduler.jobs.run_check", lambda db, monitor: None)
    result = run_due_checks(db_session, now=now)
    assert result == []


def test_one_failing_monitor_does_not_block_others(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    failing = _make_monitor(db_session, frequency="hourly", last_checked=now - timedelta(hours=2))
    healthy = _make_monitor(db_session, frequency="hourly", last_checked=now - timedelta(hours=2))

    def maybe_fail(db, monitor):
        if monitor.id == failing.id:
            raise RuntimeError("simulated fetch crash")

    monkeypatch.setattr("app.scheduler.jobs.run_check", maybe_fail)

    result = run_due_checks(db_session, now=now)
    assert healthy.id in result
    assert failing.id not in result  # it raised, so it's not in the "successfully checked" list
