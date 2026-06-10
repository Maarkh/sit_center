#!/usr/bin/env bash
# scripts/stop_demo.sh — stop the local demo stack (our processes + test containers).
#
# Kill patterns are unique to THIS project; running them from a script file (not an
# inline shell) avoids the pgrep/pkill self-match, and they never match the askbot
# container or the meeting-ai project (generic celery / .venv command lines).
set -uo pipefail
cd "$(dirname "$0")/.."

echo "▶ stopping our processes (askbot / meeting-ai untouched)"
for P in "uvicorn api.main:app" "demo-worker@" "celerybeat-schedule.db" "monitor_cpu.py" "vite --port 3010"; do
  pkill -f "$P" 2>/dev/null || true
done
sleep 2

if [ "${KEEP_DB:-0}" != "1" ]; then
  echo "▶ stopping test-db + test-redis (data persists; set KEEP_DB=1 to leave them up)"
  docker compose -f docker-compose.test.yml stop test-db test-redis >/dev/null 2>&1 || true
fi

echo "✓ stopped."
