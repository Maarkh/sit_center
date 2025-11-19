# api/routes/data.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any, Literal
from datetime import datetime, timezone
import json
import re
from api.schemas import DataPoint, DataQueryResponse, DataQueryRequest
from core.database import get_engine
from sqlalchemy import text
from api.auth import get_current_user, TokenData
from api.limiter import limiter
from config import mask_secrets, logger
from sqlalchemy import text
from sqlalchemy.sql import quoted_name

router = APIRouter(prefix="/data", tags=["Data"])
ALLOWED_DIMENSIONS = {"service", "region", "dc", "env", "team"}
ALLOWED_AGGREGATIONS = {"avg", "sum", "min", "max", "count"}
MAX_QUERY_RESULTS = 10000


def safe_jsonb_eq(column_expr: str, param_prefix: str, key: str, value: str) -> tuple[str, dict]:
    """
    Возвращает безопасное выражение: dimensions->>:key = :value
    Защищает от SQL-инъекции.
    """
    # 🔐 Валидация ключа: только [a-zA-Z0-9_-], длина 1-50
    if not isinstance(key, str) or not re.match(r"^[a-zA-Z0-9_\-]{1,50}$", key):
        from core.exceptions import InvalidDimensionKeyError
        raise InvalidDimensionKeyError(key)

    # 🔐 Валидация значения
    if not isinstance(value, str) or len(value) > 200:
        raise HTTPException(400, "Dimension value too long or invalid type")
    if '"' in value or "'" in value or '\\' in value:
        raise HTTPException(400, "Dimension value contains forbidden characters")

    return (
        f"{column_expr}->>:key_{param_prefix} = :val_{param_prefix}",
        {f"key_{param_prefix}": key, f"val_{param_prefix}": value}
    )


def validate_label_name(label_name: str) -> str:
    """Валидирует имя лейбла для защиты от injection"""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid label name: {label_name}. Use only alphanumeric and underscore."
        )
    if len(label_name) > 50:
        raise HTTPException(400, "Label name too long")
    return label_name


@router.get("/")
def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.username}


@router.get("/prometheus/api/v1/label/__name__/values", response_model=List[str])
def prometheus_label_values1():
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT DISTINCT metric_name FROM canonical_metrics ORDER BY metric_name")
            )
            return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Error fetching metric names: {mask_secrets(str(e))}")
        raise HTTPException(500, "Internal server error")


@router.get("/prometheus/api/v1/label/{label_name}/values", response_model=List[str])
def prometheus_label_values(label_name: str):
    if label_name == "__name__":
        return prometheus_label_values1()

    label_name = validate_label_name(label_name)

    if label_name not in ALLOWED_DIMENSIONS:
        raise HTTPException(
            status_code=403,
            detail=f"Dimension '{label_name}' not allowed. Allowed: {ALLOWED_DIMENSIONS}"
        )

    engine = get_engine()
    try:
        with engine.connect() as conn:
            has_key = conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM canonical_metrics WHERE dimensions ? :label_name LIMIT 1)"),
                {"label_name": label_name}
            ).scalar()
            if not has_key:
                return []

            values_query = text("""
                SELECT DISTINCT dimensions->>:label_name as value
                FROM canonical_metrics
                WHERE dimensions ? :label_name
                  AND dimensions->>:label_name IS NOT NULL
                ORDER BY value
                LIMIT 1000
            """)
            result = conn.execute(values_query, {"label_name": label_name})
            return [row[0] for row in result if row[0]]
    except Exception as e:
        logger.error(f"Error fetching label values for {label_name}: {mask_secrets(str(e))}")
        raise HTTPException(500, "Internal server error")


@router.get("/prometheus/api/v1/series", response_model=Dict[str, Any])
def prometheus_series(
    match: List[str] = Query(default=[], alias="match[]"),
    start: float = Query(None),
    end: float = Query(None)
):
    if not match:
        raise HTTPException(status_code=400, detail="match[] is required")
    
    engine = get_engine()
    series_set = set()
    
    for pattern in match:
        match_obj = re.match(r'^([a-zA-Z0-9_\-\.]+)(?:\{(.*)\})?$', pattern)
        if not match_obj:
            continue
        metric_name, filters_str = match_obj.groups()
        
        # Строим запрос с параметрами
        where_parts = ["metric_name = :metric"]
        params: Dict[str, Any] = {"metric": metric_name}
        
        if filters_str:
            for i, kv in enumerate(filters_str.split(",")):
                kv = kv.strip()
                if "=" not in kv:
                    continue
                k, v = kv.split("=", 1)
                k = k.strip()
                v = v.strip('"\'').strip()
                
                # Валидация ключа
                k = validate_label_name(k)
                if k not in ALLOWED_DIMENSIONS:
                    raise HTTPException(400, f"Dimension '{k}' not allowed")
                
                # Параметризованный запрос
                param_key = f"key_{i}"
                param_val = f"val_{i}"
                where_parts.append(f"dimensions->>:{param_key} = :{param_val}")
                params[param_key] = k
                params[param_val] = v
        
        # Безопасный запрос
        where_clause = " AND ".join(where_parts)
        query = text(f"""
            SELECT DISTINCT metric_name, dimensions
            FROM canonical_metrics
            WHERE {where_clause}
            LIMIT 1000
        """)
        
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            for row in rows:
                label_set = {"__name__": row["metric_name"]}
                label_set.update(row["dimensions"] or {})
                series_set.add(json.dumps(label_set, sort_keys=True))
    
    return {"status": "success", "data": [json.loads(s) for s in series_set]}


MAX_STEP_SECONDS = 86400


def _parse_duration(s: str) -> int:
    if not isinstance(s, str):
        raise HTTPException(400, "step must be string")
    s = s.strip()
    if len(s) > 10:
        raise HTTPException(400, "step string too long")
    match = re.fullmatch(r"^(\d{1,6})([smhd])$", s)
    if not match:
        raise HTTPException(400, "Invalid step format. Use: '15s', '1m', '2h', '1d'")
    num_str, unit = match.groups()
    num = int(num_str)
    if num <= 0:
        raise HTTPException(400, "step must be positive")
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    seconds = num * multipliers[unit]
    if seconds > 86400:
        raise HTTPException(400, "step too large (max 1 day)")
    return seconds


@router.get("/prometheus/api/v1/query_range", response_model=Dict[str, Any])
def prometheus_query_range(
    query: str,
    start: float,
    end: float,
    step: str = "15s",
    aggregation: Literal["avg", "sum", "min", "max", "count"] = "avg",
):
    match_obj = re.match(r'^([a-zA-Z0-9_\-\.]+)(?:\{(.*)\})?$', query)
    if not match_obj:
        raise HTTPException(400, "Invalid query format. Use: metric_name{label='value'}")

    metric_name, filters_str = match_obj.groups()

    from core.metadata_service import metadata_service
    valid_metrics = {m.metric_name for m in metadata_service.list_metrics(active_only=True)}
    if metric_name not in valid_metrics:
        raise HTTPException(404, f"Metric '{metric_name}' not found or inactive")

    if start >= end:
        raise HTTPException(400, "start must be before end")
    if end - start > 86400 * 30:
        raise HTTPException(400, "Time range too large (max 30 days)")

    try:
        step_sec = _parse_duration(step)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Invalid step: {mask_secrets(str(e))}")

    where = ["metric_name = :metric", "timestamp >= :start", "timestamp <= :end"]
    params = {
        "metric": metric_name,
        "start": datetime.fromtimestamp(start, tz=timezone.utc),
        "end": datetime.fromtimestamp(end, tz=timezone.utc),
        "step_sec": step_sec,
    }

    if filters_str:
        for i, kv in enumerate(filters_str.split(",")):
            kv = kv.strip()
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            v = v.strip('"\'').strip()
            if k not in ALLOWED_DIMENSIONS:
                raise HTTPException(400, f"Dimension '{k}' not allowed. Allowed: {ALLOWED_DIMENSIONS}")
            expr, p = safe_jsonb_eq("dimensions", f"filter_{i}", k, v)
            where.append(expr)
            params.update(p)

    if aggregation not in ALLOWED_AGGREGATIONS:
        aggregation = "avg"

    group_by_expr = f"floor(EXTRACT(EPOCH FROM timestamp) / :step_sec) * :step_sec"

    query_sql = text(f"""
        SELECT
            {group_by_expr} AS bin,
            dimensions,
            {aggregation}(value) AS value
        FROM canonical_metrics
        WHERE {" AND ".join(where)}
        GROUP BY bin, dimensions
        ORDER BY bin
        LIMIT :limit
    """)
    params["limit"] = MAX_QUERY_RESULTS

    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(query_sql, params).mappings().all()

        series_map = {}
        for row in rows:
            dims = tuple(sorted((k, v) for k, v in (row["dimensions"] or {}).items()))
            key = (metric_name, dims)
            if key not in series_map:
                series_map[key] = {
                    "metric": {"__name__": metric_name, **dict(dims)},
                    "values": []
                }
            series_map[key]["values"].append([
                float(row["bin"]),
                str(round(row["value"], 6))
            ])

        result = list(series_map.values())
        return {
            "status": "success",
            "data": {"resultType": "matrix", "result": result}
        }

    except Exception as e:
        logger.exception("Error executing Prometheus query")
        raise HTTPException(500, "Query execution failed")


@router.post("/query", response_model=DataQueryResponse)
@limiter.limit("30/minute")
async def query_data(
    request: DataQueryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    from core.metadata_service import metadata_service
    metric = metadata_service.get_metric(request.metric_name)
    if not metric or not metric.is_active:
        raise HTTPException(404, f"Metric '{request.metric_name}' not found")

    where = ["metric_name = :metric_name"]
    params = {"metric_name": request.metric_name}

    if request.start_time:
        where.append("timestamp >= :start")
        params["start"] = request.start_time # type: ignore
    if request.end_time:
        where.append("timestamp <= :end")
        params["end"] = request.end_time # type: ignore

    if request.dimensions:
        for i, (k, v) in enumerate(request.dimensions.items()):
            if k not in ALLOWED_DIMENSIONS:
                raise HTTPException(400, f"Dimension '{k}' not allowed")
            expr, p = safe_jsonb_eq("dimensions", f"dim_{i}", k, str(v))
            where.append(expr)
            params.update(p)

    if request.dimension_in:
        for i, (k, vals) in enumerate(request.dimension_in.items()):
            if k not in ALLOWED_DIMENSIONS:
                raise HTTPException(400, f"Dimension '{k}' not allowed")
            if not isinstance(vals, list) or len(vals) > 50:
                raise HTTPException(400, f"Too many values for {k} (max 50)")
            clean_vals = []
            for val in vals:
                val = str(val).strip()
                if '"' in val or "'" in val or len(val) > 100:
                    raise HTTPException(400, f"Invalid value in dimension_in[{k}]: {val}")
                clean_vals.append(val)
            where.append("dimensions->>:key_in = ANY(:vals_in)")
            params["key_in"] = k
            params["vals_in"] = clean_vals # type: ignore

    limit = min(request.limit, MAX_QUERY_RESULTS)
    params["limit"] = limit # type: ignore

    query = text(f"""
        SELECT timestamp, value, dimensions, tags
        FROM canonical_metrics
        WHERE {" AND ".join(where)}
        ORDER BY timestamp DESC
        LIMIT :limit
    """)

    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            points = [
                DataPoint(
                    timestamp=row["timestamp"],
                    value=float(row["value"]),
                    dimensions=row["dimensions"] or {},
                    tags=row["tags"] or {}
                )
                for row in rows
            ]
            return DataQueryResponse(
                metric_name=request.metric_name,
                points=points,
                total=len(points)
            )
    except Exception as e:
        logger.exception("Query execution error")
        raise HTTPException(500, "Query failed")