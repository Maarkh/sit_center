#!/usr/bin/env bash
# scripts/run_demo.sh — one command to (re)start the whole local demo stack on fresh code.
#
# Idempotent and reboot-safe:
#   * recreates /tmp/demo.env if missing (it lives in tmpfs, so a host reboot wipes it);
#   * brings up the test-db + test-redis containers (data persists in their volumes);
#   * restarts backend (:8010) + celery worker/beat + collector + frontend (:3010).
#
# Process kill patterns are UNIQUE to this project — they never touch the askbot
# container or the meeting-ai project, which share generic `celery -A tasks.celery_app`
# / `.venv/bin/celery` command lines. Running this from a script file (not an inline
# `bash -c`) also avoids the pgrep/pkill self-match that yields a benign exit 144.
#
#   scripts/run_demo.sh        # bring everything up / restart on latest code
#
# Logs: /tmp/{backend,celery,monitor,vite}.log   Login: admin / admin @ :3010
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
ENV_FILE="${DEMO_ENV:-/tmp/demo.env}"
VENV="$ROOT/.venv/bin"
# bcrypt("admin") — kept OUT of demo.env because the '$' chars get shell-expanded when
# the file is sourced; the backend launcher sets it inline, single-quoted.
ADMIN_HASH='$2b$12$og87/j8zmULE7nd6EUpud.rS/8xpxmW5GaciRZBG.hkHQztviVeri'

log() { printf '\n▶ %s\n' "$*"; }

# 1) demo.env — recreate only if missing (preserves SECRET_KEY across restarts)
if [ ! -f "$ENV_FILE" ]; then
  log "recreating $ENV_FILE (fresh SECRET_KEY)"
  SK="$("$VENV/python" -c 'import secrets; print(secrets.token_urlsafe(48))')"
  cat > "$ENV_FILE" <<EOF
TESTING=1
LOG_FORMAT=text
COOKIE_SECURE=false
PYTHONPATH=$ROOT
DATABASE_URL=postgresql://test_user:test_pass@localhost:5444/test_db
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_pass
POSTGRES_SERVER=localhost
POSTGRES_PORT=5444
POSTGRES_DB=test_db
REDIS_HOST=localhost
REDIS_PORT=6399
REDIS_PASSWORD=
SECRET_KEY=$SK
ADMIN_USERNAME=admin
I_DOIT_API_URL=http://localhost/api
KAFKA_ENABLED=false
CLICKHOUSE_ENABLED=false
LDAP_ENABLED=false
OIDC_ENABLED=false
SAMPLE_SECONDS=5
EVAL_EVERY_SECONDS=20
EVAL_WINDOW_MIN=1
EOF
else
  log "using existing $ENV_FILE"
fi

# 2) test containers (data persists in volumes)
log "starting test-db + test-redis"
docker compose -f docker-compose.test.yml up -d test-db test-redis >/dev/null 2>&1 || true
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' sit_center-test-db-1 2>/dev/null)" = healthy ] && break
  sleep 1
done
echo "  test-db: $(docker inspect -f '{{.State.Health.Status}}' sit_center-test-db-1 2>/dev/null)  " \
     "test-redis: $(docker inspect -f '{{.State.Health.Status}}' sit_center-test-redis-1 2>/dev/null)"

# 3) stop OUR processes only (patterns unique to this project)
log "stopping our processes (askbot / meeting-ai untouched)"
for P in "uvicorn api.main:app" "demo-worker@" "celerybeat-schedule.db" "monitor_cpu.py" "vite --port 3010"; do
  pkill -f "$P" 2>/dev/null || true
done
sleep 3

# 4) launch (each sources demo.env; detached so they survive this shell)
log "launching backend :8010"
setsid bash -c "set -a; . '$ENV_FILE'; set +a; export ADMIN_PASSWORD='$ADMIN_HASH'; exec '$VENV/uvicorn' api.main:app --host 0.0.0.0 --port 8010" \
  > /tmp/backend.log 2>&1 < /dev/null & disown

log "launching celery worker + beat"
setsid bash -c "set -a; . '$ENV_FILE'; set +a; exec '$ROOT/scripts/run_celery.sh'" \
  > /tmp/celery.log 2>&1 < /dev/null & disown

log "launching collector"
setsid bash -c "set -a; . '$ENV_FILE'; set +a; exec '$VENV/python' scripts/monitor_cpu.py" \
  > /tmp/monitor.log 2>&1 < /dev/null & disown

log "launching frontend :3010"
setsid bash -c "cd '$ROOT/frontend' && exec npx vite --port 3010 --strictPort" \
  > /tmp/vite.log 2>&1 < /dev/null & disown

# 5) wait for the backend, then report
log "waiting for readiness…"
for _ in $(seq 1 40); do curl -sf http://localhost:8010/health >/dev/null 2>&1 && break; sleep 1; done
sleep 8

rows="$(PGPASSWORD=test_pass psql -h localhost -p 5444 -U test_user -d test_db -tA \
  -c "SELECT count(*) FROM canonical_metrics WHERE source='Local host' AND timestamp > NOW() - INTERVAL '20 seconds';" 2>/dev/null)"

echo
echo "── status ──────────────────────────────────────────────"
printf '  backend  :8010   http %s\n' "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/health 2>/dev/null)"
printf '  frontend :3010   http %s\n' "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3010/ 2>/dev/null)"
if grep -q 'ready\.' /tmp/celery.log 2>/dev/null; then echo '  celery           worker ready'; else echo '  celery           starting…'; fi
printf '  collector        %s cpu/mem points in last 20s\n' "${rows:-0}"
echo "  logs: /tmp/{backend,celery,monitor,vite}.log   login: admin/admin"
echo "────────────────────────────────────────────────────────"
