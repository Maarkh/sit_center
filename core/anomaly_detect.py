# core/anomaly_detect.py
"""E: calibrated, dependency-light anomaly detection.

The previous detector (core/ml_anomaly.py) was a Prophet/IsolationForest/LSTM stack —
heavy (TF/torch, absent in many deploys) and parked because it was uncalibrated (it was
fit on the same points it scored, so its confidence was noise).

This replacement uses the **modified z-score** (Iglewicz & Hoaglin): robust to outliers
because it centres on the *median* and scales by the *MAD* (median absolute deviation),
not the mean/stdev that a single spike would inflate. Its threshold is *calibrated*: for
roughly normal data, |modified_z| > 3.5 flags ~the same tail a 3.5σ rule would, a known
operating point — not a magic number tuned on noise.

Calibration discipline (the fix for the parking reason): stats are computed on a TRAIN
window that EXCLUDES the recent SCORE window, so the baseline is never fit on the points
it judges. Pure functions here; the Celery task wires DB + persistence + alerting.
"""
import os
from statistics import median, pstdev, mean
from typing import List, Tuple, Dict, Any

# |modified z| at/above this is an anomaly. 3.5 = the classic Iglewicz–Hoaglin cutoff.
Z_THRESHOLD = float(os.environ.get("ANOMALY_Z_THRESHOLD", "3.5"))
# Need enough history to trust median/MAD; below this we don't score (avoid false alarms).
MIN_TRAIN_POINTS = int(os.environ.get("ANOMALY_MIN_TRAIN_POINTS", "20"))
# 1/0.6745 — scales MAD to be a consistent estimator of σ for normal data.
_MAD_TO_SIGMA = 1.4826


def modified_z_scores(train: List[float], score: List[float]) -> List[float]:
    """Modified z-score of each `score` value against the `train` baseline. Robust path
    uses median + MAD; if the baseline has zero MAD (e.g. a near-constant series) it falls
    back to mean/stdev; if that's also degenerate (a true constant) it returns 0s — you
    cannot statistically calibrate "how surprising" a jump is with no baseline spread."""
    if not train:
        return [0.0] * len(score)
    med = median(train)
    mad = median([abs(x - med) for x in train])
    if mad > 1e-12:
        denom = _MAD_TO_SIGMA * mad
        return [(x - med) / denom for x in score]
    sd = pstdev(train) if len(train) > 1 else 0.0
    if sd > 1e-12:
        m = mean(train)
        return [(x - m) / sd for x in score]
    return [0.0] * len(score)


def detect_anomalies(train: List[float], score_points: List[Tuple[Any, float]],
                     k: float = None) -> List[Dict[str, Any]]:
    """Flag score points whose |modified z| ≥ k. `score_points` is [(timestamp, value)].
    Returns dicts with timestamp, value, predicted (the median baseline), zscore and a
    0..1 confidence. Empty when the baseline is too small/degenerate to judge."""
    k = Z_THRESHOLD if k is None else k
    if len(train) < MIN_TRAIN_POINTS or not score_points:
        return []
    med = median(train)
    zs = modified_z_scores(train, [v for _, v in score_points])
    out = []
    for (ts, v), z in zip(score_points, zs):
        if abs(z) >= k:
            out.append({
                "timestamp": ts,
                "value": v,
                "predicted": med,
                "zscore": z,
                # squash |z| into 0..1: exactly at threshold ≈0.5, saturating toward 1.
                "confidence": min(1.0, 0.5 + (abs(z) - k) / (2 * k)),
            })
    return out
