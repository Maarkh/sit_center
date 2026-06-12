"""B: auto-provision baseline indicators — pure selection logic + task gating."""
import importlib


def test_select_drops_covered_and_blank():
    from core.auto_provision import _select_to_provision
    ready = ["cpu_usage", "mem_usage", "disk_usage", "", "rps"]
    covered = {"mem_usage"}
    out = _select_to_provision(ready, covered, cap=10)
    assert out == ["cpu_usage", "disk_usage", "rps"]  # sorted, covered+blank dropped


def test_select_caps_batch():
    from core.auto_provision import _select_to_provision
    ready = [f"m{i:02d}" for i in range(20)]
    out = _select_to_provision(ready, set(), cap=5)
    assert len(out) == 5
    assert out == ["m00", "m01", "m02", "m03", "m04"]  # deterministic order


def test_select_empty_when_all_covered():
    from core.auto_provision import _select_to_provision
    assert _select_to_provision(["a", "b"], {"a", "b"}) == []


def test_env_flag_parsing(monkeypatch):
    monkeypatch.setenv("AUTO_PROVISION_INDICATORS", "true")
    import core.auto_provision as ap
    importlib.reload(ap)
    assert ap.AUTO_PROVISION_ENABLED is True
    monkeypatch.setenv("AUTO_PROVISION_INDICATORS", "false")
    importlib.reload(ap)
    assert ap.AUTO_PROVISION_ENABLED is False
