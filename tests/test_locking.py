# tests/test_locking.py
"""Unit tests for the distributed-lock helpers (single_run / global_lock).

A fake Redis-ish cache stands in for the real client: set(nx) + eval(Lua) are the
only primitives the lock uses, so we can exercise acquire / skip / release purely
in-process, no Redis required.
"""
import core.locking as locking
from core.locking import single_run, global_lock


class FakeCache:
    """Minimal SETNX + Lua-eval cache: enough for the lock's CAS unlock/extend."""

    def __init__(self):
        self.store = {}

    def set(self, key, value, nx=False, px=None, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def get(self, key):
        return self.store.get(key)

    def eval(self, script, numkeys, key, value, *args):
        # Both the unlock and the extend scripts are CAS: act only if we still own it.
        if self.store.get(key) != value:
            return 0
        if "del" in script:
            self.store.pop(key, None)
        return 1


def _use_fake_cache(monkeypatch):
    cache = FakeCache()
    monkeypatch.setattr(locking, "get_cache", lambda: cache)
    return cache


def test_single_run_executes_and_releases(monkeypatch):
    _use_fake_cache(monkeypatch)
    calls = []

    @single_run("t:run")
    def task():
        calls.append(1)
        return {"did": "work"}

    assert task() == {"did": "work"}
    # Lock released in finally → a second, non-overlapping run proceeds normally.
    assert task() == {"did": "work"}
    assert calls == [1, 1]


def test_single_run_skips_when_already_held(monkeypatch):
    cache = _use_fake_cache(monkeypatch)
    # Simulate a previous run still holding the lock.
    cache.set("lock_t:busy", "another-worker", nx=True, px=1000)

    calls = []

    @single_run("t:busy")
    def task():
        calls.append(1)
        return {"did": "work"}

    assert task() == {"skipped_locked": True}
    assert calls == []  # body never ran


def test_global_lock_nonblocking_returns_false_when_held(monkeypatch):
    cache = _use_fake_cache(monkeypatch)
    cache.set("lock_t:x", "owner", nx=True, px=1000)
    with global_lock("t:x", blocking=False) as acquired:
        assert acquired is False


def test_global_lock_blocking_yields_true_and_frees(monkeypatch):
    cache = _use_fake_cache(monkeypatch)
    with global_lock("t:y", timeout=1) as acquired:
        assert acquired is True
        assert "lock_t:y" in cache.store
    # released on exit
    assert "lock_t:y" not in cache.store
