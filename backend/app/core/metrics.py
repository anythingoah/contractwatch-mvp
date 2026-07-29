"""
Prometheus metrics. Kept to exactly the five things ops actually needs to
watch for this product — request volume/latency, and the three numbers
that answer "is monitoring actually working": jobs executed, checks
failed, alerts sent. Resist the urge to add more without a concrete
dashboard/alert that needs them.
"""
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

http_requests_total = Counter(
    "contractwatch_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "contractwatch_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

scheduler_jobs_executed_total = Counter(
    "contractwatch_scheduler_jobs_executed_total",
    "Monitor checks executed by the scheduler",
)

monitor_check_failed_total = Counter(
    "contractwatch_monitor_check_failed_total",
    "Monitor checks that raised an exception or found the target unreachable",
    ["reason"],  # "unreachable" | "exception"
)

alerts_sent_total = Counter(
    "contractwatch_alerts_sent_total",
    "Alerts dispatched, by channel type and outcome",
    ["channel_type", "outcome"],  # outcome: "success" | "failure"
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
