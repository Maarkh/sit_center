"""E: calibrated robust-z anomaly detection — pure logic + calibration discipline."""
from core.anomaly_detect import modified_z_scores, detect_anomalies, MIN_TRAIN_POINTS


def _clean(n=50, val=100.0):
    return [val + (i % 5 - 2) * 0.1 for i in range(n)]  # tiny jitter around 100


def test_clean_series_has_no_anomalies():
    train = _clean(60)
    score = [("t1", 100.0), ("t2", 100.1)]
    assert detect_anomalies(train, score) == []


def test_spike_is_flagged():
    train = _clean(60)                       # baseline ~100 ± 0.x
    score = [("t1", 100.0), ("t2", 250.0)]   # 250 is a gross outlier
    out = detect_anomalies(train, score)
    assert len(out) == 1
    a = out[0]
    assert a["timestamp"] == "t2" and a["value"] == 250.0
    assert a["zscore"] > 3.5 and 0.5 <= a["confidence"] <= 1.0
    assert abs(a["predicted"] - 100.0) < 1.0   # baseline median ≈ 100


def test_mad_uses_median_not_mean_robust_to_train_outliers():
    # one huge value already in the TRAIN set must not blind the detector (mean/stdev would)
    train = _clean(59) + [10000.0]
    out = detect_anomalies(train, [("t", 250.0)])
    assert len(out) == 1  # median/MAD ignores the lone 10000, still flags 250


def test_constant_baseline_yields_no_false_positive():
    # zero spread → cannot calibrate surprise → no anomaly (documented limitation)
    train = [42.0] * 40
    assert detect_anomalies(train, [("t", 99.0)]) == []
    assert modified_z_scores(train, [99.0]) == [0.0]


def test_too_little_history_skips():
    train = [100.0 + i * 0.01 for i in range(MIN_TRAIN_POINTS - 1)]
    assert detect_anomalies(train, [("t", 9999.0)]) == []


def test_negative_direction_also_flagged():
    train = _clean(60)
    out = detect_anomalies(train, [("t", -500.0)])
    assert len(out) == 1 and out[0]["zscore"] < -3.5
