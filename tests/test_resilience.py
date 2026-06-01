# tests/test_resilience.py
"""Tests for graceful degradation: Redis fallback, i-doit retry queue."""
from unittest.mock import patch, MagicMock


class TestRedisFallback:
    def test_returns_default_on_redis_error(self):
        from core.resilience import redis_fallback

        @redis_fallback(default=[])
        def get_cached_data():
            raise ConnectionError("Redis down")

        result = get_cached_data()
        assert result == []

    def test_returns_normal_value_when_ok(self):
        from core.resilience import redis_fallback

        @redis_fallback(default=[])
        def get_cached_data():
            return [1, 2, 3]

        result = get_cached_data()
        assert result == [1, 2, 3]

    def test_callable_default(self):
        from core.resilience import redis_fallback

        @redis_fallback(default=dict)
        def get_data():
            raise ConnectionError("Redis down")

        result = get_data()
        assert result == {}


class TestSafeIdoitPush:
    def test_swallows_errors(self):
        from core.resilience import safe_idoit_push

        @safe_idoit_push
        def push_data():
            raise RuntimeError("i-doit connection refused")

        with patch("celery_app.celery_app") as mock_celery:
            mock_celery.send_task = MagicMock()
            result = push_data()
            assert result is None

    def test_passes_through_on_success(self):
        from core.resilience import safe_idoit_push

        @safe_idoit_push
        def push_data():
            return "ok"

        result = push_data()
        assert result == "ok"
