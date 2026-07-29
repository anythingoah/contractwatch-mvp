"""
Structured (JSON) logging setup. One place to configure it; every module
just does `logger = logging.getLogger("contractwatch.<module>")` and logs
normally — no per-module setup needed.

In production, point your log collector (Fly logs, Railway logs, whatever)
at stdout and it'll pick up JSON lines directly — no separate log shipper
config needed for an MVP-scale deployment.
"""
import logging
import json
import sys
from datetime import datetime, timezone

from app.core.request_context import get_request_id


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Allow call sites to attach structured context: logger.info("msg", extra={"cw_monitor_id": 5})
        for key, value in record.__dict__.items():
            if key.startswith("cw_"):
                payload[key.removeprefix("cw_")] = value
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers at INFO
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
