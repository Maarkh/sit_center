# tests/test_ml.py
import pytest
from core.ml_anomaly import detect_anomaly_prophet_isolation_group, MIN_POINTS
import pandas as pd


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "timestamp": pd.date_range(start="2023-01-01", periods=50, freq="h"),
        "value": [i + (10 if i % 10 == 0 else 0) for i in range(50)]  # С аномалиями
    })


def test_detect_anomaly_prophet(sample_df):
    anomalies = detect_anomaly_prophet_isolation_group(sample_df, dimensions={"region": "test"})
    assert isinstance(anomalies, list)
    assert len(anomalies) > 0
    assert "timestamp" in anomalies[0]


def test_empty_df_returns_empty():
    """Пустой df не должен падать — guard возвращает []."""
    df = pd.DataFrame({"timestamp": pd.to_datetime([]), "value": []})
    assert detect_anomaly_prophet_isolation_group(df, dimensions={"region": "x"}) == []


def test_too_few_points_returns_empty():
    """Меньше MIN_POINTS точек — возврат [] до обучения Prophet."""
    n = MIN_POINTS - 1
    df = pd.DataFrame({
        "timestamp": pd.date_range(start="2023-01-01", periods=n, freq="h"),
        "value": list(range(n)),
    })
    assert detect_anomaly_prophet_isolation_group(df, dimensions={"region": "x"}) == []


def test_duplicate_timestamps_collapse_below_min():
    """50 строк с одинаковым timestamp схлопываются дедупом ниже MIN_POINTS -> []."""
    ts = pd.Timestamp("2023-01-01 00:00:00")
    df = pd.DataFrame({
        "timestamp": [ts] * 50,
        "value": list(range(50)),
    })
    assert detect_anomaly_prophet_isolation_group(df, dimensions={"region": "x"}) == []
