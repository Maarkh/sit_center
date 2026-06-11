# tests/test_forecast_drift.py
"""Unit tests for forecast drift math (pure functions — no DB)."""
from datetime import datetime, timezone, timedelta

from core.forecast_drift import error_metrics, align_pairs

T0 = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestErrorMetrics:
    def test_empty(self):
        m = error_metrics([])
        assert m == {"n": 0, "mae": None, "rmse": None, "mape": None}

    def test_perfect_prediction(self):
        m = error_metrics([(10.0, 10.0), (20.0, 20.0)])
        assert m["n"] == 2 and m["mae"] == 0.0 and m["rmse"] == 0.0 and m["mape"] == 0.0

    def test_known_errors(self):
        # errors: |10-12|=2, |20-16|=4 → MAE=3; RMSE=sqrt((4+16)/2)=sqrt(10)
        m = error_metrics([(10.0, 12.0), (20.0, 16.0)])
        assert m["mae"] == 3.0
        assert abs(m["rmse"] - (10 ** 0.5)) < 1e-6
        # MAPE = mean(2/12, 4/16)*100 = mean(0.16667,0.25)*100 = 20.8333%
        assert abs(m["mape"] - 20.8333) < 0.01

    def test_mape_skips_zero_actuals(self):
        # actual 0 is skipped for MAPE (no div-by-zero); MAE/RMSE still include it
        m = error_metrics([(1.0, 0.0), (10.0, 8.0)])
        assert m["n"] == 2
        assert abs(m["mape"] - 25.0) < 0.01   # only the (10,8) pair: 2/8=25%

    def test_mape_none_when_all_actuals_zero(self):
        m = error_metrics([(1.0, 0.0), (2.0, 0.0)])
        assert m["mape"] is None and m["mae"] == 1.5


class TestAlignPairs:
    def _series(self, *mins_vals):
        return [(T0 + timedelta(minutes=mm), v) for mm, v in mins_vals]

    def test_exact_match(self):
        fpoints = [(T0 + timedelta(minutes=5), 100.0)]
        actuals = self._series((0, 90.0), (5, 110.0), (10, 95.0))
        assert align_pairs(fpoints, actuals, tol_seconds=600) == [(100.0, 110.0)]

    def test_nearest_within_tolerance(self):
        # forecast at +6m; nearest actual is +5m (60s away) ≤ tol → matched
        fpoints = [(T0 + timedelta(minutes=6), 100.0)]
        actuals = self._series((0, 90.0), (5, 110.0))
        assert align_pairs(fpoints, actuals, tol_seconds=120) == [(100.0, 110.0)]

    def test_dropped_outside_tolerance(self):
        # nearest actual is 10m (600s) away, tol 120s → dropped
        fpoints = [(T0 + timedelta(minutes=15), 100.0)]
        actuals = self._series((0, 90.0), (5, 110.0))
        assert align_pairs(fpoints, actuals, tol_seconds=120) == []

    def test_empty_actuals(self):
        assert align_pairs([(T0, 1.0)], [], tol_seconds=600) == []
