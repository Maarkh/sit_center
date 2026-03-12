# core/analytics_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import logger, mask_secrets


class AnalyticsService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from core.clickhouse import get_clickhouse_client
            self._client = get_clickhouse_client()
        return self._client

    def query_metric_aggregation(
        self,
        metric_name: str,
        start: datetime,
        end: datetime,
        aggregation: str = "avg",
        interval: str = "1 HOUR",
        tenant_id: str = "default",
        dimension_filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        allowed_aggs = {"avg", "sum", "min", "max", "count"}
        if aggregation not in allowed_aggs:
            aggregation = "avg"

        query = f"""
            SELECT
                toStartOfInterval(timestamp, INTERVAL {interval}) AS bucket,
                {aggregation}(value) AS agg_value,
                count() AS sample_count
            FROM sit_center.metrics
            WHERE metric_name = {{metric_name:String}}
              AND timestamp >= {{start:DateTime64(3)}}
              AND timestamp <= {{end:DateTime64(3)}}
              AND tenant_id = {{tenant_id:String}}
            GROUP BY bucket
            ORDER BY bucket
        """
        params = {
            "metric_name": metric_name,
            "start": start,
            "end": end,
            "tenant_id": tenant_id,
        }

        try:
            client = self._get_client()
            result = client.query(query, parameters=params)
            return [
                {"bucket": str(row[0]), "value": row[1], "count": row[2]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error("ClickHouse query_metric_aggregation failed: %s", mask_secrets(str(e)))
            return []

    def query_top_n_metrics(
        self,
        start: datetime,
        end: datetime,
        n: int = 10,
        tenant_id: str = "default",
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT
                metric_name,
                count() AS cnt,
                avg(value) AS avg_value,
                max(value) AS max_value
            FROM sit_center.metrics
            WHERE timestamp >= {start:DateTime64(3)}
              AND timestamp <= {end:DateTime64(3)}
              AND tenant_id = {tenant_id:String}
            GROUP BY metric_name
            ORDER BY cnt DESC
            LIMIT {n:UInt32}
        """
        params = {"start": start, "end": end, "tenant_id": tenant_id, "n": n}

        try:
            client = self._get_client()
            result = client.query(query, parameters=params)
            return [
                {"metric_name": row[0], "count": row[1], "avg_value": row[2], "max_value": row[3]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error("ClickHouse query_top_n_metrics failed: %s", mask_secrets(str(e)))
            return []

    def query_alert_statistics(
        self,
        start: datetime,
        end: datetime,
        tenant_id: str = "default",
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT
                metric_name,
                status,
                count() AS cnt
            FROM sit_center.alerts
            WHERE event_time >= {start:DateTime64(3)}
              AND event_time <= {end:DateTime64(3)}
              AND tenant_id = {tenant_id:String}
            GROUP BY metric_name, status
            ORDER BY cnt DESC
        """
        params = {"start": start, "end": end, "tenant_id": tenant_id}

        try:
            client = self._get_client()
            result = client.query(query, parameters=params)
            return [
                {"metric_name": row[0], "status": row[1], "count": row[2]}
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error("ClickHouse query_alert_statistics failed: %s", mask_secrets(str(e)))
            return []


analytics_service = AnalyticsService()
