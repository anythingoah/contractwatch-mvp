"""
End-to-end test of monitors/service.run_check: fetch -> normalize -> hash ->
diff -> classify -> store Change rows -> dispatch alerts. Fetchers are
monkeypatched so no real network call happens.
"""
from app.models import User, Monitor, MonitorType, Change
from app.monitors import service


def _make_user_and_monitor(db_session) -> Monitor:
    user = User(email="pipeline@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()
    monitor = Monitor(user_id=user.id, name="Pipeline Test", type=MonitorType.mcp,
                       mcp_server_url="https://mcp.example.com", mcp_transport="http")
    db_session.add(monitor)
    db_session.commit()
    return monitor


def test_first_check_creates_baseline_with_no_changes(db_session, monkeypatch):
    monitor = _make_user_and_monitor(db_session)

    monkeypatch.setattr(
        "app.monitors.service.fetch_mcp_tools",
        lambda url, transport: {"tools": [{"name": "search", "inputSchema": {"properties": {}, "required": []}}]},
    )

    result = service.run_check(db_session, monitor)
    assert result["status"] == "baseline_created"
    assert result["changes_detected"] == 0
    assert db_session.query(Change).count() == 0


def test_second_check_with_breaking_change_creates_change_and_alerts(db_session, monkeypatch):
    monitor = _make_user_and_monitor(db_session)

    responses = iter([
        {"tools": [{"name": "create_invoice", "inputSchema": {
            "properties": {"amount": {"type": "number"}, "currency": {"type": "string"}},
            "required": ["amount", "currency"],
        }}]},
        {"tools": [{"name": "create_invoice", "inputSchema": {
            "properties": {"amount": {"type": "number"}},
            "required": ["amount"],
        }}]},
    ])
    monkeypatch.setattr("app.monitors.service.fetch_mcp_tools", lambda url, transport: next(responses))

    alerts_fired = []
    monkeypatch.setattr(
        "app.monitors.service.dispatch_alerts",
        lambda db, mon, changes, severity: alerts_fired.append(severity),
    )

    service.run_check(db_session, monitor)  # baseline
    result = service.run_check(db_session, monitor)  # drift

    assert result["status"] == "changes_detected"
    assert result["breaking"] is True
    assert db_session.query(Change).count() == 1
    assert db_session.query(Change).first().severity.value == "critical"
    assert alerts_fired == ["critical"]


def test_unchanged_contract_produces_no_diff(db_session, monkeypatch):
    monitor = _make_user_and_monitor(db_session)
    fixed_response = {"tools": [{"name": "search", "inputSchema": {"properties": {}, "required": []}}]}
    monkeypatch.setattr("app.monitors.service.fetch_mcp_tools", lambda url, transport: fixed_response)

    service.run_check(db_session, monitor)  # baseline
    result = service.run_check(db_session, monitor)  # identical again

    assert result["status"] == "no_change"
    assert db_session.query(Change).count() == 0


def test_unreachable_endpoint_marks_monitor_unreachable(db_session, monkeypatch):
    from app.fetchers.mcp_fetcher import FetchError
    monitor = _make_user_and_monitor(db_session)

    def raise_fetch_error(url, transport):
        raise FetchError("connection refused")

    monkeypatch.setattr("app.monitors.service.fetch_mcp_tools", raise_fetch_error)

    result = service.run_check(db_session, monitor)
    assert result["status"] == "unreachable"
    db_session.refresh(monitor)
    assert monitor.status.value == "unreachable"
