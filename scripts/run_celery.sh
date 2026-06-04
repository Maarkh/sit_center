#!/usr/bin/env bash
# Run the Celery worker + beat for the local prod-like demo, against the
# docker-compose.test.yml stack (test-db :5444, test-redis :6399).
#
# This is what makes the local setup behave like production: the monitor only
# collects metrics, while Celery beat schedules the DSS tasks (evaluate, correlate,
# predict, escalate, SLA breaches) and the worker executes them — same code paths
# and the same celeryconfig.beat_schedule as prod.
#
#   scripts/run_celery.sh           # foreground; Ctrl-C stops both
#   scripts/run_celery.sh > /tmp/celery.log 2>&1 &   # background
#
# ML tasks (core.ml_tasks.*) route to the 'ml' queue and are intentionally not run
# here; start a second worker with `-Q ml` if you need them.
set -euo pipefail
cd "$(dirname "$0")/.."

# Test-stack connection (matches docker-compose.test.yml). Override via env if needed.
export DATABASE_URL="${DATABASE_URL:-postgresql://test_user:test_pass@localhost:5444/test_db}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6399}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-}"
export TESTING="${TESTING:-1}"
export LOG_FORMAT="${LOG_FORMAT:-text}"
export SECRET_KEY="${SECRET_KEY:-demo-secret-key-0123456789abcdef}"
export KAFKA_ENABLED=false CLICKHOUSE_ENABLED=false LDAP_ENABLED=false OIDC_ENABLED=false

VENV="${VENV:-.venv/bin}"
echo "▶ Celery worker + beat against ${DATABASE_URL} (redis ${REDIS_HOST}:${REDIS_PORT})"

"$VENV/celery" -A tasks.celery_app worker --loglevel=info --concurrency=2 -Q celery -n demo-worker@%h &
WORKER=$!
"$VENV/celery" -A tasks.celery_app beat --loglevel=info --schedule /tmp/celerybeat-schedule.db &
BEAT=$!

trap 'echo "stopping..."; kill "$WORKER" "$BEAT" 2>/dev/null' INT TERM
wait
