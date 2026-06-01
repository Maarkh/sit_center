# tests/test_logging.py
"""Tests for structured JSON logging."""
import json
import logging
from config import JsonFormatter


class TestJsonFormatter:
    def test_formats_as_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=(), exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "hello world"
        assert "timestamp" in data

    def test_masks_secrets_in_message(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="connecting to redis://:secret123@host:6379", args=(), exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert "secret123" not in data["message"]
        assert "***" in data["message"]

    def test_includes_request_id_when_set(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="request", args=(), exc_info=None,
        )
        record.request_id = "abc123"  # type: ignore
        result = formatter.format(record)
        data = json.loads(result)
        assert data["request_id"] == "abc123"

    def test_no_request_id_when_not_set(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert "request_id" not in data

    def test_includes_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("test error with password=secret123")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="failed", args=(), exc_info=exc_info,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert "exception" in data
        assert "secret123" not in data["exception"]
