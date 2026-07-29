"""
Fans a set of changes out to every configured alert channel for a monitor.
"""
import logging

from sqlalchemy.orm import Session

from app.models import Monitor, AlertChannel, ChannelType
from app.alerts.slack import send_slack_alert
from app.alerts.email import send_email_alert
from app.alerts.webhook import send_webhook_alert
from app.core.metrics import alerts_sent_total

logger = logging.getLogger("contractwatch.alerts")


def dispatch_alerts(db: Session, monitor: Monitor, changes: list[dict], severity: str) -> None:
    channels = db.query(AlertChannel).filter(AlertChannel.monitor_id == monitor.id).all()

    for channel in channels:
        config = channel.configuration or {}
        ok = False
        if channel.type == ChannelType.slack:
            ok = send_slack_alert(config.get("webhook_url", ""), monitor.name, changes)
        elif channel.type == ChannelType.email:
            ok = send_email_alert(config.get("email", ""), monitor.name, changes)
        elif channel.type == ChannelType.webhook:
            ok = send_webhook_alert(config.get("url", ""), monitor.name, severity, changes)

        alerts_sent_total.labels(channel_type=channel.type.value, outcome="success" if ok else "failure").inc()

        log_fn = logger.info if ok else logger.error
        log_fn(
            "Alert dispatch %s" % ("succeeded" if ok else "failed"),
            extra={
                "cw_monitor_id": monitor.id,
                "cw_channel_type": channel.type.value,
                "cw_channel_id": channel.id,
            },
        )
