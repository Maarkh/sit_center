# Makefile — control the local Situational Center demo stack.
# Backend runs on :8010 (the meeting-ai project owns :8000 on this host).
# Open http://localhost:3010 and log in as admin / admin.
.PHONY: help up restart down status logs test
.DEFAULT_GOAL := help
SHELL := /bin/bash
COMPOSE := docker compose -f docker-compose.test.yml

help: ## list available commands
	@grep -hE '^[a-z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  make %-9s %s\n", $$1, $$2}'

up: ## (re)start the whole stack on fresh code — reboot-safe
	@scripts/run_demo.sh

restart: up ## alias for `up` (run_demo.sh kills + relaunches)

down: ## stop our processes + test containers (askbot/meeting-ai untouched)
	@scripts/stop_demo.sh

status: ## show stack health
	@printf 'backend  :8010  http %s\n' "$$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/health 2>/dev/null || echo DOWN)"
	@printf 'frontend :3010  http %s\n' "$$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3010/ 2>/dev/null || echo DOWN)"
	@$(COMPOSE) ps test-db test-redis 2>/dev/null || true

logs: ## tail backend / celery / collector / vite logs (Ctrl-C to stop)
	@tail -n 30 -f /tmp/backend.log /tmp/celery.log /tmp/monitor.log /tmp/vite.log

test: ## run the backend test suite
	@LOG_FORMAT=text TESTING=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_ml.py --ignore=tests/integration -q
