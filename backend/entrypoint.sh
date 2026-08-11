#!/bin/sh
# Start the app. Keeps "docker compose up" working as a one-command bootstrap.
set -e
# No --reload flag — debug auto-reload is a local-dev concern only (see README).
exec uvicorn app.main:app --host 0.0.0.0 --port 3000
