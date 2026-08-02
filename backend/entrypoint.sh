#!/bin/sh
# Run pending migrations, then start the app. Keeps "docker compose up"
# working as a one-command bootstrap without needing create_all() anymore.
set -e
alembic upgrade head
# No --reload flag — debug auto-reload is a local-dev concern only (see README).
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
