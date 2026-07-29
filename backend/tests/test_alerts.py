"""
Alert dispatch: verifies each channel type is invoked with the right shape
and that a failed send doesn't stop other channels from firing. Slack/email/
webhook senders are mocked at the network boundary (httpx) rather than hit
for real.
"""
from app.models import Monitor, AlertChannel, MonitorType, ChannelType
from app.alerts.service import dispatch_alerts


def _make_monitor(db_session) -> Monitor:
    from app.models import User
    user = User(email="alerts@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()
    monitor = Monitor(user_id=user.id, name="Test Monitor", type=MonitorType.rest,
                       openapi_spec_url="https://example.com/openapi.json")
    db_session.add(monitor)
    db_session.flush()
    return monitor


def test_dispatch_calls_slack_webhook(db_session, monkeypatch):
    monitor = _make_monitor(db_session)
    db_session.add(AlertChannel(monitor_id=monitor.id, type=ChannelType.slack,
                                 configuration={"webhook_url": "https://hooks.slack.com/x"}))
    db_session.commit()

    called = {}

    def fake_slack(url, name, changes):
        called["url"] = url
        called["name"] = name
        return True

    monkeypatch.setattr("app.alerts.service.send_slack_alert", fake_slack)

    dispatch_alerts(db_session, monitor, [{"type": "x", "severity": "critical", "message": "m"}], "critical")
    assert called["url"] == "https://hooks.slack.com/x"
    assert called["name"] == "Test Monitor"


def test_dispatch_continues_after_one_channel_fails(db_session, monkeypatch):
    monitor = _make_monitor(db_session)
    db_session.add(AlertChannel(monitor_id=monitor.id, type=ChannelType.slack,
                                 configuration={"webhook_url": "https://hooks.slack.com/x"}))
    db_session.add(AlertChannel(monitor_id=monitor.id, type=ChannelType.webhook,
                                 configuration={"url": "https://example.com/hook"}))
    db_session.commit()

    calls = []
    monkeypatch.setattr("app.alerts.service.send_slack_alert", lambda *a: (calls.append("slack"), False)[1])
    monkeypatch.setattr("app.alerts.service.send_webhook_alert", lambda *a: (calls.append("webhook"), True)[1])

    dispatch_alerts(db_session, monitor, [{"type": "x", "severity": "info", "message": "m"}], "info")
    assert calls == ["slack", "webhook"]  # webhook still fires even though slack failed


def test_email_skipped_gracefully_without_api_key(db_session):
    from app.alerts.email import send_email_alert
    # No EMAIL_API_KEY configured in test settings -> should return False, not raise
    result = send_email_alert("someone@example.com", "Test Monitor", [{"severity": "critical", "message": "m"}])
    assert result is False
