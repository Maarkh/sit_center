import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import logging
import joblib
from config import get_cache, settings, logger, mask_secrets
from core.metric_service import load_metrics_from_db_cached
from core.database import get_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from core.models import MLAnomaly, MetadataMLConfig, MetadataMetric
from core.metadata_service import MLConfigDTO, metadata_service, get_or_create_default_ml_configs
from core.utils import serialize_anomalies
from tenacity import retry, stop_after_attempt, wait_exponential
import psutil  # Для мониторинга памяти
import gc
try:
    import tensorflow as tf
    from prophet import Prophet
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from tensorflow.keras.models import Sequential 
    from tensorflow.keras.layers import LSTM, Dense
    from sklearn.cluster import DBSCAN
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logger.warning("ML libraries missing — anomaly detection disabled")

from contextlib import contextmanager
import re
import sys
import os

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

SAFE_DIMENSION_KEY_RE = re.compile(r"^[a-zA-Z0-9_]{1,50}$")
from pathlib import Path

ML_MODEL_DIR = Path("/app/models")
logger = logging.getLogger(__name__)
device = 'cuda' if HAS_TORCH and torch.cuda.is_available() else 'cpu'


# Ключи кэша
MODEL_CACHE_KEY = "ml_model_{metric}_{region}"
ANOMALY_CACHE_KEY = "ml_last_anomaly_{metric}_{region}"

# Порог уверенности аномалии (Isolation Forest)
ANOMALY_THRESHOLD = -0.5

# Минимальное количество точек для обучения
MIN_POINTS = 48

def _get_model_path(metric_name: str, group_key: str) -> Path:
    ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in f"{metric_name}_{group_key}")
    return ML_MODEL_DIR / f"{safe_key}.pkl"

def save_model(model, metric_name: str, group_key: str) -> str:
    path = _get_model_path(metric_name, group_key)
    try:
        joblib.dump(model, path)
        version = f"{int(datetime.now().timestamp())}"
        return version
    except Exception as e:
        logger.error(f"❌ Не удалось сохранить модель {path}: {e}")
        raise

def load_model(metric_name: str, group_key: str) -> Optional[Any]:
    path = _get_model_path(metric_name, group_key)
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки {path}: {e}")
        return None

@contextmanager
def suppress_stdout():
    """Подавляет stdout (Prophet слишком болтлив)"""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def detect_anomaly_prophet_isolation(
    df: pd.DataFrame,
    metric_col: str,
    region_col: str = "region",
    ts_col: str = "timestamp"
) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []
    """
    Обнаружение аномалий: Prophet (остатки) + Isolation Forest.
    Возвращает список аномальных точек с меткой времени и регионом.
    """
    anomalies = []
    cache = get_cache()  # Получаем кэш один раз перед циклом

    for region in df[region_col].unique():
        region_data = df[df[region_col] == region].copy()
        if len(region_data) < MIN_POINTS:
            continue

        # Подготовка данных для Prophet
        prophet_df = region_data[[ts_col, metric_col]].rename(
            columns={ts_col: "ds", metric_col: "y"}
        )
        if prophet_df["ds"].dt.tz is not None:
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)
        prophet_df = prophet_df.dropna().sort_values("ds")

        if len(prophet_df) < MIN_POINTS:
            continue

        # Убираем дубликаты по времени (если есть)
        prophet_df = prophet_df.groupby("ds").agg({"y": "mean"}).reset_index()

        try:
            # Prophet: модель с ежечасной сезонностью
            model = Prophet( # type: ignore
                daily_seasonality=True, # type: ignore
                weekly_seasonality=True, # type: ignore
                yearly_seasonality=False, # type: ignore
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0
            )
            model.fit(prophet_df)
            
            # Предсказание и остатки
            forecast = model.predict(prophet_df[["ds"]])
            prophet_df["yhat"] = forecast["yhat"].values
            prophet_df["residual"] = prophet_df["y"] - prophet_df["yhat"]
            prophet_df["abs_residual"] = prophet_df["residual"].abs()

            # Isolation Forest на остатках + значение y
            features = prophet_df[["y", "abs_residual"]].values
            iso_forest = IsolationForest(contamination=0.1, random_state=42) # type: ignore
            anomaly_labels = iso_forest.fit_predict(features)  # 1 = норма, -1 = аномалия

            # Сохраняем модель
            model_key = MODEL_CACHE_KEY.format(metric=metric_col, region=region)
            model_bytes = joblib.dumps(model) # type: ignore
            cache.set(model_key, model_bytes, ex=60 * 60 * 24 * 7)  # 7 дней вместо 24 часов

            # Фильтруем аномалии
            anomalous_points = prophet_df[anomaly_labels == -1]
            for _, row in anomalous_points.iterrows():
                anomalies.append({
                    "region": region,
                    "metric": metric_col,
                    "timestamp": row["ds"].to_pydatetime(),
                    "value": row["y"],
                    "predicted": row["yhat"],
                    "residual": row["residual"]
                })

        except Exception as e:
            logger.error(f"ML anomaly failed for {region}/{metric_col}: {mask_secrets(str(e))}", exc_info=True)
            raise  

    return anomalies


def find_recent_ml_anomalies(time_filter="6h", metrics=None, methods=None):
    if methods is None:
        methods = settings.ml_methods or ["prophet", "lstm", "clustering"]

    delta_map = {"1h": 1, "6h": 6, "24h": 24, "2d": 48, "5d": 120}
    hours = delta_map.get(time_filter, 6)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    engine = get_engine()

    active_metrics = {m.metric_name for m in metadata_service.list_metrics(active_only=True)}
    target_metrics = set(metrics) if metrics else active_metrics

    query_base = """
        SELECT
            metric_name,
            value,
            timestamp,
            dimensions,
            tags
        FROM canonical_metrics
        WHERE metric_name = ANY(:metrics)
          AND timestamp >= :cutoff
        ORDER BY timestamp
    """

    # Пагинация
    rows = []
    offset = 0
    batch_size = 10000
    with engine.connect() as conn:
        while True:
            batch_query = text(query_base + " OFFSET :offset LIMIT :batch_size")
            batch = conn.execute(batch_query, {
                "metrics": list(target_metrics),
                "cutoff": cutoff,
                "offset": offset,
                "batch_size": batch_size
            }).mappings().all()
            if not batch:
                break
            rows.extend(batch)
            offset += batch_size

    if not rows:
        logger.warning(f"Нет данных за {time_filter} для метрик: {target_metrics}")
        return []

    df = pd.DataFrame(rows)
    df = df[df["value"].between(df["value"].quantile(0.01), df["value"].quantile(0.99))]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    if df.empty:
        return []

    df["dimensions"] = df["dimensions"].apply(lambda x: x if isinstance(x, dict) else {})
    df["tags"] = df["tags"].apply(lambda x: x if isinstance(x, dict) else {})

    all_anomalies = []

    max_workers = min(settings.ML_MAX_WORKERS or 4, os.cpu_count() or 4)

    for metric in target_metrics:
        metric_df = df[df["metric_name"] == metric]
        if metric_df.empty:
            continue

        ml_configs = [cfg for cfg in metadata_service.list_active_ml_configs() if cfg.metric_name == metric]
        ml_configs = ml_configs or get_or_create_default_ml_configs(metric)

        for cfg in ml_configs:
            try:
                group_by = cfg.group_by or ["region"]
                group_by = [g for g in group_by if metric_df["dimensions"].apply(lambda d: g in d).any()]

                if not group_by:
                    groups = [("all", metric_df)]
                else:
                    def extract_key(row):
                        return tuple(row["dimensions"].get(k, "N/A") for k in group_by)
                    
                    metric_df["_group_key"] = metric_df.apply(extract_key, axis=1)
                    groups = list(metric_df.groupby("_group_key"))
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    process_func = partial(process_group_batch, cfg=cfg)
                    futures = []
                    for group_key, group_df in groups:
                        if psutil.virtual_memory().percent > 80:
                            logger.warning(f"High memory ({psutil.virtual_memory().percent}%) — skipping {group_key}")
                            continue
                        futures.append(executor.submit(process_func, (group_key, group_df)))
                    
                    for future in as_completed(futures):
                        try:
                            anomalies = future.result(timeout=60)
                            all_anomalies.extend(anomalies)
                        except TimeoutError:
                            logger.warning("Timeout processing group")
                        except Exception as e:
                            logger.error(f"Error processing group: {mask_secrets(str(e))}")
            
            except Exception as e:
                logger.error(f"Ошибка ML для {metric}, group={cfg.group_by}: {mask_secrets(str(e))}")

    if all_anomalies:
        Session = sessionmaker(bind=engine)
        with Session() as session:
            try:
                for a in all_anomalies:
                    anomaly = MLAnomaly(
                        metric_name=a["metric_name"],
                        dimensions=a["dimensions"],
                        timestamp=a["timestamp"],
                        value=a["value"],
                        predicted=a.get("predicted"),
                        residual=a.get("residual"),
                        confidence=a.get("confidence"),
                        method=a["method"]
                    )
                    session.add(anomaly)
                session.commit()
                logger.info(f"✅ Сохранено {len(all_anomalies)} ML-аномалий")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения: {mask_secrets(str(e))}")
                session.rollback()

    get_cache().set("ml_anomalies", serialize_anomalies(all_anomalies), ex=300)
    return all_anomalies


# Вспомогательные функции для групп
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def detect_anomaly_prophet_isolation_group(df: pd.DataFrame, dimensions: Dict) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []
    
    # Подготовка данных для Prophet
    prophet_df = df[["timestamp", "value"]].rename(
        columns={"timestamp": "ds", "value": "y"}
    ).copy()
    
    # Корректная обработка timezone
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    
    # Prophet требует tz-naive, но сохраняем смысл времени
    if prophet_df["ds"].dt.tz is not None:
        prophet_df["ds"] = prophet_df["ds"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    # Сортировка и удаление дубликатов
    prophet_df = prophet_df.dropna().sort_values("ds")
    prophet_df = prophet_df.drop_duplicates(subset="ds", keep="last")
    
    if len(prophet_df) < MIN_POINTS:
        return []
    
    try:
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )
        
        with suppress_stdout():
            model.fit(prophet_df)

        try:
            from prophet.diagnostics import cross_validation, performance_metrics
            if len(prophet_df) >= 100:
                with suppress_stdout():
                    df_cv = cross_validation(
                        model,
                        initial='15 days',
                        period='3 days',
                        horizon='7 days',
                        parallel="processes"
                    )
                    df_perf = performance_metrics(df_cv)
                
                cv_mape = df_perf['mape'].mean()
                if cv_mape > 0.3:
                    logger.warning(f"CV MAPE={cv_mape:.1%} >30% для {dimensions} — модель ненадежна")
                    return []
                logger.info(f"✅ CV MAPE={cv_mape:.1%} для {dimensions}")
        except ImportError:
            logger.debug("prophet.diagnostics недоступен — пропуск CV")
        except Exception as e:
            logger.warning(f"Ошибка кросс-валидации: {e}")

        forecast = model.predict(prophet_df[["ds"]])
        prophet_df["yhat"] = forecast["yhat"].values
        prophet_df["yhat_lower"] = forecast["yhat_lower"].values
        prophet_df["yhat_upper"] = forecast["yhat_upper"].values
        prophet_df["residual"] = prophet_df["y"] - prophet_df["yhat"]
        prophet_df["abs_residual"] = prophet_df["residual"].abs()
        
        mape = np.mean(np.abs((prophet_df["y"] - prophet_df["yhat"]) / prophet_df["y"])) * 100
        if mape > 30:
            logger.warning(f"Prophet MAPE={mape:.1f}% >30% для {dimensions} — пропуск")
            return []
        
        features = prophet_df[["y", "abs_residual"]].values
        iso = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        labels = iso.fit_predict(features)
        
        anomalies = []
        for idx, row in prophet_df[labels == -1].iterrows():
            ts = pd.Timestamp(row["ds"], tz="UTC")
            anomalies.append({
                "timestamp": ts.to_pydatetime(),
                "value": float(row["y"]),
                "predicted": float(row["yhat"]),
                "residual": float(row["residual"]),
                "confidence": float(iso.decision_function(features)[idx])
            })
        
        return anomalies
    
    except Exception as e:
        logger.warning(f"Prophet failed для {dimensions}: {e}")
        raise

def detect_anomaly_lstm_group(df: pd.DataFrame, dimensions: Dict) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []
    
    # Ограничение памяти
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            logger.warning(f"GPU memory setup failed: {e}")
    
    if len(df) < 48:
        return []
    
    values = df['value'].values.reshape(-1, 1)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(values)

    def create_sequences(data, seq_length=24):
        xs, ys = [], []
        for i in range(len(data) - seq_length):
            xs.append(data[i:(i + seq_length)])
            ys.append(data[i + seq_length])
        return np.array(xs), np.array(ys)

    seq_length = 24
    X, y = create_sequences(scaled, seq_length)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = None

    model = Sequential([
        LSTM(50, activation='relu', input_shape=(seq_length, 1)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    try:
        model.fit(X, y, epochs=10, verbose=0, batch_size=32)
        predictions = model.predict(X, verbose=0)
        mse = np.mean(np.power(y - predictions, 2), axis=1)
        threshold = np.mean(mse) + 3 * np.std(mse)

        anomalies = []
        for i in range(len(mse)):
            if mse[i] > threshold:
                anomalies.append({
                    'timestamp': df.iloc[i + seq_length]['timestamp'],
                    'value': values[i + seq_length][0],
                    'predicted': scaler.inverse_transform(predictions[i].reshape(-1, 1))[0][0],
                    'residual': mse[i],
                    'confidence': 1 - (mse[i] - np.min(mse)) / (np.max(mse) - np.min(mse)) if np.max(mse) > np.min(mse) else 0.5
                })
        return anomalies
    except Exception as e:
        logger.error(f"LSTM detection failed: {e}")
        return []
    finally:
        # Обязательная очистка
        if model:
            del model
        tf.keras.backend.clear_session()
        gc.collect()

def detect_anomaly_clustering_group(df: pd.DataFrame, dimensions: Dict) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []    

    lat = dimensions.get("lat")
    lon = dimensions.get("lon")
    if not (lat and lon):
        return []

    if 'value' not in df.columns or len(df) < 3:
        return []

    # Предполагаем, что df имеет lat/lon в dimensions, но для group — агрегируем? Или per-row
    # Адаптируем: Добавим lat/lon в df если нужно, но поскольку dimensions — для группы, пропустим или используйте coords из data
    # Пример: Если df имеет 'lat', 'lon'
    if 'lat' not in df.columns or 'lon' not in df.columns:
        return []

    df = df.dropna(subset=['lat', 'lon', 'value'])

    coords = df[['lat', 'lon']].values
    values = df['value'].values.reshape(-1, 1)

    X = np.hstack([coords, values * 0.1])  # Scale

    clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
    labels = clustering.labels_

    anomalies = []
    for i, label in enumerate(labels):
        if label == -1:
            row = df.iloc[i]
            anomalies.append({
                'timestamp': row['timestamp'],
                'value': row['value'],
                'predicted': None,  # No predicted in clustering
                'residual': None,
                'confidence': clustering.core_sample_indices_[i] if i in clustering.core_sample_indices_ else 0,
                'method': 'clustering'
            })
    return anomalies


def get_ml_model_status() -> Dict[str, List[str]]:
    """
    Возвращает статус обученных моделей (для дебага/админки).
    """
    cache = get_cache()
    metrics = [m.column for m in load_metrics_from_db_cached()]
    regions = cache.get("regions") or ["Moscow", "SPb"]

    trained = []
    for m in metrics:
        for r in regions:  # type: ignore
            key = MODEL_CACHE_KEY.format(metric=m, region=r)
            if cache.get(key):
                trained.append(f"{m} -> {r}")
    return {"trained_models": trained}

def detect_anomaly_lstm(region_data, metric_col, window_size=24):
    if not HAS_ML_LIBS:
        return []    
    """Обнаружение аномалий с помощью LSTM"""
    try:
        # Подготовка данных
        values = region_data[metric_col].values
        if len(values) < window_size * 2:
            return []
        
        # Нормализация
        scaler = StandardScaler()
        scaled_values = scaler.fit_transform(values.reshape(-1, 1)).flatten()
        
        # Создание окон данных
        X, y = [], []
        for i in range(len(scaled_values) - window_size):
            X.append(scaled_values[i:i+window_size])
            y.append(scaled_values[i+window_size])
        
        X, y = np.array(X), np.array(y)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Построение модели LSTM
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(window_size, 1)),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        
        # Обучение модели
        model.fit(X, y, epochs=10, verbose=0)
        
        # Прогнозирование
        predictions = model.predict(X, verbose=0)
        
        # Вычисление ошибок прогнозирования
        errors = np.abs(y - predictions.flatten())
        
        # Определение аномалий (ошибка > 2 стандартных отклонения)
        threshold = np.mean(errors) + 2 * np.std(errors)
        anomalies = []
        
        for i in range(len(errors)):
            if errors[i] > threshold:
                anomalies.append({
                    'timestamp': region_data.iloc[i+window_size]['timestamp'],
                    'value': values[i+window_size],
                    'predicted': scaler.inverse_transform([[predictions[i][0]]])[0][0],
                    'error': errors[i]
                })
        
        return anomalies
        
    except Exception as e:
        logger.warning(f"LSTM anomaly detection failed: {e}")
        return []

def detect_anomaly_clustering(df: pd.DataFrame, metric_col: str) -> List[Dict]:
    if not HAS_ML_LIBS:
        return []    

    # Проверим, есть ли lat/lon в df
    if 'lat' not in df.columns or 'lon' not in df.columns:
        logger.warning("Нет координат 'lat'/'lon' в данных. Пропуск кластеризации.")
        return []

    # Фильтруем только строки с данными
    df = df.dropna(subset=['lat', 'lon', metric_col])

    if len(df) < 3:
        return []

    coords = df[['lat', 'lon']].values
    values = df[metric_col].values.reshape(-1, 1) # type: ignore

    # Объединяем координаты и значения
    X = np.hstack([coords, values * 0.1])  # масштабируем значение

    clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
    labels = clustering.labels_

    anomalies = []
    for i, label in enumerate(labels):
        if label == -1:  # шум = аномалия
            row = df.iloc[i]
            anomalies.append({
                'region': row['region'],
                'metric': metric_col,
                'timestamp': row['timestamp'],
                'value': row[metric_col],
                'lat': row['lat'],
                'lon': row['lon'],
                'cluster_method': 'DBSCAN'
            })
    return anomalies
    
    
def retrain_all_models():
    logger.info("Начало переобучения ML-моделей")
    engine = get_engine()
    Session = sessionmaker(bind=engine)

    if not HAS_ML_LIBS:
        return []    

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.ml_model_cache_days)

    with Session() as session:
        # Загружаем активные ML-конфиги
        ml_configs = (
            session.query(MetadataMLConfig)
            .join(MetadataMetric)
            .filter(
                MetadataMLConfig.is_active.is_(True),
                MetadataMetric.is_active.is_(True)
            )
            .all()
        )

        if not ml_configs:
            logger.info("Нет активных ML-конфигураций для переобучения.")
            return

        for cfg in ml_configs:
            metric_name = cfg.metric_name
            group_by_keys = cfg.group_by or ["region"]

            # Валидация dimension keys для защиты от SQL injection
            for key in group_by_keys:
                if not SAFE_DIMENSION_KEY_RE.match(key):
                    logger.error(f"Invalid dimension key: {key}, skipping config {cfg.id}")
                    continue

            logger.info(f"Переобучение: {metric_name}, group_by={group_by_keys}")

            # Безопасное построение запроса: ключи валидированы regex выше
            dim_select = ", ".join(
                f"dimensions->>'{key}' as \"{key}\"" for key in group_by_keys
            )
            dim_filter = " AND ".join(
                f"dimensions->>'{key}' IS NOT NULL" for key in group_by_keys
            )

            query = text(f"""
            SELECT
                timestamp,
                value,
                {dim_select}
            FROM canonical_metrics
            WHERE metric_name = :metric_name
              AND timestamp >= :cutoff
              AND {dim_filter}
            ORDER BY timestamp
            LIMIT 10000
            """)

            df = pd.read_sql(
                query,
                engine,
                params={"metric_name": metric_name, "cutoff": cutoff}
            )

            if df.empty:
                logger.info(f"Нет данных для {metric_name}")
                continue

            # Группируем по group_by
            group_cols = [col for col in group_by_keys if col in df.columns]
            if not group_cols:
                continue

            for group_tuple, group_df in df.groupby(group_cols):
                if len(group_df) < MIN_POINTS:
                    continue

                # Приводим к формату Prophet
                prophet_df = group_df[["timestamp", "value"]].copy()
                prophet_df = prophet_df.rename(columns={"timestamp": "ds", "value": "y"})
                prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
                prophet_df = prophet_df.dropna().sort_values("ds")

                if len(prophet_df) < MIN_POINTS:
                    continue

                try:
                    model = Prophet(
                        daily_seasonality=True,
                        weekly_seasonality=True,
                        yearly_seasonality=False,
                        changepoint_prior_scale=0.05,
                        seasonality_prior_scale=10.0
                    )
                    model.fit(prophet_df)

                    # Формируем ключ кэша
                    group_key = "_".join(str(v) for v in group_tuple) if isinstance(group_tuple, tuple) else str(group_tuple)
                    cache_key = f"ml_model:{metric_name}:{group_key}"

                    cache = get_cache()
                    cache.set(cache_key, joblib.dumps(model), ex=60*60*24*settings.ml_model_cache_days)

                    logger.info(f"Модель переобучена: {cache_key}")

                except Exception as e:
                    logger.error(f"Ошибка обучения модели {metric_name}/{group_key}: {e}")

    logger.info("Переобучение ML-моделей завершено")

def process_group_batch(group_data: tuple, cfg: MLConfigDTO) -> List[Dict]:
    """
    Обрабатывает одну группу данных для ML-аномалий.
    
    Args:
        group_data: (group_key, group_df)
        cfg: ML-конфигурация
    
    Returns:
        Список аномалий
    """
    group_key, group_df = group_data
    
    if len(group_df) < MIN_POINTS:
        return []
    
    dims = dict(zip(cfg.group_by, group_key)) if cfg.group_by else {}
    all_anomalies = []
    
    try:
        # Prophet
        if "prophet" in cfg.methods:
            anomalies = detect_anomaly_prophet_isolation_group(group_df, dims)
            for a in anomalies:
                a.update({
                    "metric_name": cfg.metric_name,
                    "dimensions": dims,
                    "method": "prophet"
                })
            all_anomalies.extend(anomalies)
        
        # LSTM
        if "lstm" in cfg.methods and len(group_df) >= 48:
            anomalies = detect_anomaly_lstm_group(group_df, dims)
            for a in anomalies:
                a.update({
                    "metric_name": cfg.metric_name,
                    "dimensions": dims,
                    "method": "lstm"
                })
            all_anomalies.extend(anomalies)
        
        # Clustering
        if "clustering" in cfg.methods and "lat" in dims and "lon" in dims:
            anomalies = detect_anomaly_clustering_group(group_df, dims)
            for a in anomalies:
                a.update({
                    "metric_name": cfg.metric_name,
                    "dimensions": dims,
                    "method": "clustering"
                })
            all_anomalies.extend(anomalies)
    
    except Exception as e:
        logger.error(f"Ошибка обработки группы {dims}: {e}")
    
    return all_anomalies