# tests/test_deviation_engine.py
"""Unit tests for DSS M3 corridor classification (pure functions — no DB)."""

from core.deviation_engine import classify_breach, breach_severity, fingerprint_for


class TestClassifyBreach:
    def test_inside_corridor_no_breach(self):
        assert classify_breach(50.0, 0.0, 100.0, "both") is None

    def test_below_breach(self):
        assert classify_breach(-5.0, 0.0, 100.0, "both") == "below"

    def test_above_breach(self):
        assert classify_breach(150.0, 0.0, 100.0, "both") == "above"

    def test_direction_below_ignores_above(self):
        # watching only the lower bound: an over-shoot is not a breach
        assert classify_breach(150.0, 0.0, 100.0, "below") is None
        assert classify_breach(-5.0, 0.0, 100.0, "below") == "below"

    def test_direction_above_ignores_below(self):
        assert classify_breach(-5.0, 0.0, 100.0, "above") is None
        assert classify_breach(150.0, 0.0, 100.0, "above") == "above"

    def test_one_sided_corridor_high_only(self):
        # latency: only an upper bound
        assert classify_breach(250.0, None, 200.0, "above") == "above"
        assert classify_breach(150.0, None, 200.0, "above") is None

    def test_one_sided_corridor_low_only(self):
        # availability: only a lower bound
        assert classify_breach(98.0, 99.0, None, "below") == "below"
        assert classify_breach(99.5, 99.0, None, "below") is None

    def test_boundary_values_are_inside(self):
        # exactly on the bound is NOT a breach (strict < / >)
        assert classify_breach(0.0, 0.0, 100.0, "both") is None
        assert classify_breach(100.0, 0.0, 100.0, "both") is None


class TestBreachSeverity:
    def test_small_margin_is_warning(self):
        # corridor width 100; margin 5 < 50 → warning
        assert breach_severity(-5.0, 0.0, 100.0, "below") == "warning"

    def test_large_margin_is_critical(self):
        # corridor width 100; margin 60 > 50 → critical
        assert breach_severity(160.0, 0.0, 100.0, "above") == "critical"

    def test_one_sided_uses_bound_magnitude(self):
        # high-only corridor: ref = |200| = 200; margin 150 > 100 → critical
        assert breach_severity(350.0, None, 200.0, "above") == "critical"
        # margin 50 < 100 → warning
        assert breach_severity(250.0, None, 200.0, "above") == "warning"

    def test_zero_reference_defaults_warning(self):
        # degenerate corridor (low==high==0) → no division blow-up, warning
        assert breach_severity(5.0, 0.0, 0.0, "above") == "warning"


def test_fingerprint_is_stable_per_indicator():
    fp1 = fingerprint_for("abc")
    fp2 = fingerprint_for("abc")
    assert fp1 == fp2 == "ind:abc"
    assert fingerprint_for("xyz") != fp1


class TestDeviationRBAC:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get("/api/v1/deviations/")
        assert resp.status_code in (401, 403)

    def test_viewer_lacks_read_deviations(self, api_client, viewer_auth_headers):
        resp = api_client.get("/api/v1/deviations/", headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_viewer_cannot_acknowledge(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/api/v1/deviations/00000000-0000-0000-0000-000000000000/acknowledge",
            json={}, headers=viewer_auth_headers,
        )
        assert resp.status_code == 403
