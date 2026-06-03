# tests/test_situation_engine.py
"""Unit tests for DSS M4 correlation logic (pure — no DB) + route gates."""
from datetime import datetime, timedelta, timezone

from core.situation_engine import correlate, compute_impact, root_cause

T0 = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)


def _dev(id_, indicator, minutes=0):
    return {"id": id_, "indicator_id": indicator, "detected_at": T0 + timedelta(minutes=minutes)}


class TestCorrelate:
    def test_same_indicator_within_window_clusters(self):
        devs = [_dev("a", "I1", 0), _dev("b", "I1", 5)]
        clusters = correlate(devs, [], window_seconds=600)
        assert len(clusters) == 1
        assert {d["id"] for d in clusters[0]} == {"a", "b"}

    def test_same_indicator_outside_window_splits(self):
        devs = [_dev("a", "I1", 0), _dev("b", "I1", 60)]
        clusters = correlate(devs, [], window_seconds=600)
        assert len(clusters) == 2

    def test_connected_indicators_cluster(self):
        # I1 → I2 dependency; deviations on each within window correlate
        devs = [_dev("a", "I1", 0), _dev("b", "I2", 3)]
        clusters = correlate(devs, [("I1", "I2")], window_seconds=600)
        assert len(clusters) == 1

    def test_unconnected_indicators_do_not_cluster(self):
        devs = [_dev("a", "I1", 0), _dev("b", "I2", 3)]
        clusters = correlate(devs, [], window_seconds=600)  # no edge
        assert len(clusters) == 2

    def test_transitive_component(self):
        # I1→I2→I3 ; deviations on I1 and I3 share a component
        devs = [_dev("a", "I1", 0), _dev("b", "I3", 4)]
        clusters = correlate(devs, [("I1", "I2"), ("I2", "I3")], window_seconds=600)
        assert len(clusters) == 1

    def test_chain_merge_over_time(self):
        # a~b (5m) and b~c (5m) within window even if a~c is 10m → all one cluster
        devs = [_dev("a", "I1", 0), _dev("b", "I1", 5), _dev("c", "I1", 10)]
        clusters = correlate(devs, [], window_seconds=360)
        assert len(clusters) == 1
        assert len(clusters[0]) == 3


class TestComputeImpact:
    def test_severity_weighting(self):
        crit = compute_impact([("I1", "critical")], {})
        warn = compute_impact([("I1", "warning")], {})
        assert crit == 2.0 and warn == 1.0

    def test_downstream_influence_raises_impact(self):
        # I1 influences others (out_weight 3) → higher impact than an isolated indicator
        infl = compute_impact([("I1", "warning")], {"I1": 3.0})
        iso = compute_impact([("I2", "warning")], {})
        assert infl > iso
        assert infl == 1.0 * (1.0 + 3.0)

    def test_sums_over_cluster(self):
        assert compute_impact([("I1", "critical"), ("I2", "warning")], {}) == 3.0


class TestRootCause:
    def test_upstream_source_is_root(self):
        # I1 → I2 → I3 ; I1 is the upstream-most → root cause
        earliest = {"I1": T0, "I2": T0 + timedelta(minutes=2), "I3": T0 + timedelta(minutes=4)}
        rc = root_cause({"I1", "I2", "I3"}, [("I1", "I2"), ("I2", "I3")], earliest)
        assert rc == "I1"

    def test_no_internal_edges_picks_earliest(self):
        earliest = {"I1": T0 + timedelta(minutes=5), "I2": T0}
        rc = root_cause({"I1", "I2"}, [], earliest)
        assert rc == "I2"

    def test_tie_break_by_earliest_detection(self):
        # two sources I1, I3 both point into I2; earliest detected wins
        earliest = {"I1": T0 + timedelta(minutes=3), "I2": T0 + timedelta(minutes=4), "I3": T0}
        rc = root_cause({"I1", "I2", "I3"}, [("I1", "I2"), ("I3", "I2")], earliest)
        assert rc == "I3"


class TestSituationRBAC:
    def test_list_requires_auth(self, api_client):
        assert api_client.get("/api/v1/situations/").status_code in (401, 403)

    def test_viewer_cannot_read(self, api_client, viewer_auth_headers):
        assert api_client.get("/api/v1/situations/", headers=viewer_auth_headers).status_code == 403

    def test_viewer_cannot_add_dependency(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/api/v1/situations/dependencies",
            json={"src_indicator_id": "00000000-0000-0000-0000-000000000001",
                  "dst_indicator_id": "00000000-0000-0000-0000-000000000002"},
            headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_self_dependency_rejected(self, api_client, auth_headers):
        same = "00000000-0000-0000-0000-000000000001"
        resp = api_client.post(
            "/api/v1/situations/dependencies",
            json={"src_indicator_id": same, "dst_indicator_id": same},
            headers=auth_headers)
        assert resp.status_code == 422
