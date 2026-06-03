# tests/test_predictive_engine.py
"""Unit tests for DSS M5 breach projection (pure — no DB, no ML libs) + route gates."""
from core.predictive_engine import project_breach


def _pt(ts, yhat, low=None, high=None):
    return {"ts": ts, "yhat": yhat, "yhat_low": low, "yhat_high": high}


class TestProjectBreach:
    def test_no_breach_when_forecast_stays_inside(self):
        pts = [_pt(1, 50, 45, 55), _pt(2, 52, 47, 57)]
        assert project_breach(pts, 0, 100, "both") is None

    def test_central_breach_above_is_high_confidence(self):
        pts = [_pt(1, 50, 40, 60), _pt(2, 120, 110, 130)]
        r = project_breach(pts, 0, 100, "above")
        assert r["direction"] == "above"
        assert r["ts"] == 2
        assert r["confidence"] == "high"
        assert r["projected_value"] == 120

    def test_band_only_breach_is_medium_confidence(self):
        # yhat stays under 100 but the upper band crosses → early, lower-confidence warning
        pts = [_pt(1, 80, 70, 90), _pt(2, 95, 90, 105)]
        r = project_breach(pts, 0, 100, "above")
        assert r["ts"] == 2
        assert r["confidence"] == "medium"

    def test_below_breach_uses_lower_band(self):
        pts = [_pt(1, 10, 5, 15), _pt(2, 3, -2, 8)]
        r = project_breach(pts, 0, None, "below")
        assert r["direction"] == "below"
        assert r["confidence"] == "medium"  # yhat=3 still >= 0

    def test_below_central_breach_high_confidence(self):
        pts = [_pt(1, 10, 5, 15), _pt(2, -5, -10, 0)]
        r = project_breach(pts, 0, None, "below")
        assert r["confidence"] == "high"

    def test_direction_filter_ignores_other_side(self):
        # only watching the lower bound; an upper-band excursion must not fire
        pts = [_pt(1, 95, 90, 130)]
        assert project_breach(pts, 0, 100, "below") is None

    def test_returns_first_breaching_point(self):
        pts = [_pt(1, 50, 40, 60), _pt(2, 130, 120, 140), _pt(3, 200, 190, 210)]
        r = project_breach(pts, 0, 100, "above")
        assert r["ts"] == 2

    def test_missing_band_falls_back_to_yhat(self):
        pts = [_pt(1, 150)]  # no band
        r = project_breach(pts, 0, 100, "above")
        assert r["confidence"] == "high"
        assert r["projected_value"] == 150


class TestPredictiveRBAC:
    def test_list_requires_auth(self, api_client):
        assert api_client.get("/api/v1/predictions/").status_code in (401, 403)

    def test_viewer_lacks_read_predictions(self, api_client, viewer_auth_headers):
        resp = api_client.get("/api/v1/predictions/", headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_viewer_cannot_run(self, api_client, viewer_auth_headers):
        resp = api_client.post("/api/v1/predictions/run",
                               json={"indicator_id": "00000000-0000-0000-0000-000000000000"},
                               headers=viewer_auth_headers)
        assert resp.status_code == 403
