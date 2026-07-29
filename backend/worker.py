"""
Standalone scheduler process. Run this instead of (not alongside) the
embedded scheduler once you scale to more than one API replica — set
RUN_SCHEDULER_IN_APP=false on every API instance when using this.

Usage:
    python worker.py

Docker:
    docker compose --profile worker up worker

Handles SIGTERM (what Docker/Kubernetes send on `stop`) as well as SIGINT
(Ctrl-C) — both trigger a graceful shutdown that waits for any in-progress
check to finish before exiting, so a container restart never abandons a
check mid-flight.
"""
import time
import signal
import logging

from app.core.logging_config import configure_logging
from app.scheduler.jobs import start_scheduler, stop_scheduler

configure_logging()
logger = logging.getLogger("contractwatch.worker")

_shutdown_requested = False


def _handle_shutdown_signal(signum, frame):
    global _shutdown_requested
    logger.info("Received shutdown signal", extra={"cw_signal": signum})
    _shutdown_requested = True


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_shutdown_signal)
    signal.signal(signal.SIGINT, _handle_shutdown_signal)

    logger.info("Starting standalone ContractWatch scheduler worker")
    start_scheduler()

    while not _shutdown_requested:
        time.sleep(1)

    logger.info("Shutting down worker")
    stop_scheduler()
