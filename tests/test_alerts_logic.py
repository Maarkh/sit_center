# tests/test_alerts_logic.py
import pytest
from core.alerts import generate_alert_hash, is_steady_increase


def test_generate_alert_hash():
    h = generate_alert_hash("cpu", "Moscow", 42.0)
    assert isinstance(h, str)
    assert len(h) == 32


def test_generate_alert_hash_deterministic():
    h1 = generate_alert_hash("cpu", "Moscow", 42.0)
    h2 = generate_alert_hash("cpu", "Moscow", 42.0)
    assert h1 == h2


def test_generate_alert_hash_different_inputs():
    h1 = generate_alert_hash("cpu", "Moscow", 42.0)
    h2 = generate_alert_hash("cpu", "SPb", 42.0)
    assert h1 != h2


def test_is_steady_increase_true():
    assert is_steady_increase([1, 2, 3]) is True
    assert is_steady_increase([10, 20, 30, 40]) is True


def test_is_steady_increase_false():
    assert is_steady_increase([3, 2, 1]) is False
    assert is_steady_increase([1, 3, 2]) is False
    assert is_steady_increase([1, 2]) is False  # less than 3 elements


def test_alert_suppression(fake_redis_instance):
    from core.alerts import suppress_alert, is_alert_suppressed
    suppress_alert("test_hash", 60)
    assert is_alert_suppressed("test_hash") is True


def test_alert_not_suppressed(fake_redis_instance):
    from core.alerts import is_alert_suppressed
    assert is_alert_suppressed("nonexistent_hash") is False
