# tests/test_pubsub.py
from unittest.mock import patch, MagicMock
from core.pubsub import publish_alert, ALERT_CHANNEL
import json


def test_publish_alert_calls_redis():
    mock_redis = MagicMock()
    with patch("core.pubsub.redis.from_url", return_value=mock_redis):
        data = {"type": "alert", "metric": "cpu", "value": 99.0}
        publish_alert(data)
        mock_redis.publish.assert_called_once_with(
            ALERT_CHANNEL,
            json.dumps(data, ensure_ascii=False, default=str),
        )
        mock_redis.close.assert_called_once()


def test_publish_alert_handles_error():
    with patch("core.pubsub.redis.from_url", side_effect=Exception("connection failed")):
        # Should not raise
        publish_alert({"type": "alert"})
