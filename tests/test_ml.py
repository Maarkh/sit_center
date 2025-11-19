# tests/test_ml.py
import pytest
from core.ml_anomaly import detect_anomaly_prophet_isolation_group
import pandas as pd

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "timestamp": pd.date_range(start="2023-01-01", periods=50, freq="H"),
        "value": [i + (10 if i % 10 == 0 else 0) for i in range(50)]  # С аномалиями
    })

def test_detect_anomaly_prophet(sample_df):
    anomalies = detect_anomaly_prophet_isolation_group(sample_df, dimensions={"region": "test"})
    assert len(anomalies) > 0
    assert "timestamp" in anomalies[0]