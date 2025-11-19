# core/data.py
import pandas as pd
from config import settings, logger, get_cache, mask_secrets
from datetime import datetime, timedelta
from sqlalchemy import text
import io
from core.database import get_engine
from core.metadata_service import metadata_service


cache = get_cache()
CACHE_TTL = settings.cache_ttl

def create_mv():
    if not cache.exists("data_from_db_1h_zero"):
        logger.info("Создаем MV для данных из БД")
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_hourly_region_metrics;"))
            conn.execute(text("""
                CREATE MATERIALIZED VIEW mv_hourly_region_metrics AS
                    SELECT
                    date_trunc('hour', timestamp AT TIME ZONE 'UTC') AS hour,
                    dimensions->>'region' AS region,
                    metric_name,
                    AVG(value) AS avg_value,
                    MAX(value) AS max_value,
                    COUNT(*) AS sample_count
                    FROM canonical_metrics
                    WHERE dimensions ? 'region'
                    GROUP BY 1, 2, 3;"""))

            conn.execute(text("""CREATE UNIQUE INDEX ON mv_hourly_region_metrics (hour, region, metric_name);"""))

def get_data_from_db(time_filter: str = "1h", fill_missing: str = "zero") -> pd.DataFrame:
    """Загружает данные из PostgreSQL с улучшенной обработкой ошибок"""
    key = f"data_from_db_{time_filter}_{fill_missing}"

    try:
        data = cache.get(key)
        if data:
            df = pd.read_json(io.StringIO(data), orient="split") # type: ignore
            logger.debug(f"Данные загружены из Redis: {key}")
            return df
    except Exception as e:
        logger.warning(f"Ошибка загрузки из Redis: {mask_secrets(str(e))}")

    try:
        engine = get_engine()
        now = datetime.now()
        time_deltas = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "2d": timedelta(days=2),
            "3d": timedelta(days=3),
            "5d": timedelta(days=5),
            "10d": timedelta(days=10),
        }
        cutoff = now - time_deltas.get(time_filter, timedelta(hours=1))

        # 🔴 ИСПРАВЛЕНО: динамический SELECT по метрикам из metadata_metrics
        metrics = [m.metric_name for m in metadata_service.list_metrics(active_only=True)]
        if not metrics:
            logger.warning("⚠️ Нет активных метрик для загрузки")
            metrics = ["complaints", "closed"]  # fallback

        case_expressions = [
            f"MAX(CASE WHEN cm.metric_name = '{m}' THEN cm.value END) AS {m}"
            for m in metrics
        ]
        select_clause = ",\n        ".join(case_expressions)

        query = text(f"""
            SELECT
                cm.timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'UTC' AS timestamp,
                cm.dimensions->>'region' AS region,
                {select_clause}
            FROM canonical_metrics cm
            WHERE cm.metric_name = ANY(:metrics)
              AND cm.timestamp >= :cutoff
              AND cm.dimensions ? 'region'
            GROUP BY timestamp, cm.dimensions->>'region'
            ORDER BY timestamp DESC
        """)

        df_raw = pd.read_sql(query, engine, params={"cutoff": cutoff, "metrics": metrics}) # type: ignore

        cache.setex(key, CACHE_TTL, df_raw.to_json(orient="split"))
        return df_raw.copy()

    except Exception as e:
        logger.error(f"Ошибка загрузки данных из БД: {e}")
        regions_df = pd.read_csv(settings.data_regions_path)
        regions_df["error"] = True
        regions_df["error_message"] = str(e)
        return regions_df