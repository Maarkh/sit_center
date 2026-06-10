# api/routes/forecasts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from api.schemas import ForecastResponse, ForecastPoint
from api.auth import TokenData
from core.rbac import require_permission
from config import logger, mask_secrets

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get("/predict", response_model=ForecastResponse)
def predict_metric(
    metric_name: str = Query(...),
    horizon_hours: int = Query(24, ge=1, le=168),
    region: Optional[str] = Query(None),
    current_user: TokenData = Depends(require_permission("read:metrics")),
):
    """Generate a forecast for a metric using the trained Prophet model.

    Returns predicted values with confidence intervals for the requested horizon.
    """
    from core.metadata_service import metadata_service

    valid_metrics = {
        m.metric_name
        for m in metadata_service.list_metrics(active_only=True, tenant_id=current_user.tenant_id)
    }
    if metric_name not in valid_metrics:
        raise HTTPException(404, f"Metric '{metric_name}' not found or inactive")

    dimensions: Dict[str, str] = {}
    if region:
        dimensions["region"] = region

    try:
        points = _generate_forecast(metric_name, dimensions, horizon_hours, current_user.tenant_id)
    except ImportError:
        raise HTTPException(501, "ML libraries not available for forecasting")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Forecast failed for {metric_name}: {mask_secrets(str(e))}")
        raise HTTPException(500, "Forecast generation failed")

    return ForecastResponse(
        metric_name=metric_name,
        dimensions=dimensions,
        horizon_hours=horizon_hours,
        points=points,
    )


def _generate_forecast(metric_name: str, dimensions: Dict[str, str], horizon_hours: int, tenant_id: str = "default"):
    """Try cached model first, fall back to fitting on recent data."""
    import pandas as pd

    try:
        from prophet import Prophet
    except ImportError:
        raise ImportError("Prophet is not installed")

    from core.database import get_engine
    from sqlalchemy import text
    from config import get_cache

    # Try to load a pre-trained model from cache
    group_key = "_".join(f"{k}={v}" for k, v in sorted(dimensions.items())) or "all"
    cache_key = f"ml_model:{tenant_id}:{metric_name}:{group_key}"
    cache = get_cache()
    model_bytes = cache.get(cache_key)
    model = None

    if model_bytes:
        try:
            from core.secure_pickle import loads_signed
            model = loads_signed(model_bytes)  # HMAC-verified before deserialization
        except Exception:
            model = None

    if model is None:
        # Fit a lightweight model on recent data
        engine = get_engine()
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)

        where = ["metric_name = :metric", "timestamp >= :cutoff", "tenant_id = :tenant_id"]
        params: dict = {"metric": metric_name, "cutoff": cutoff, "tenant_id": tenant_id}

        if dimensions.get("region"):
            where.append("dimensions->>'region' = :region")
            params["region"] = dimensions["region"]

        query = text(f"""
            SELECT timestamp AS ds, value AS y
            FROM canonical_metrics
            WHERE {' AND '.join(where)}
            ORDER BY timestamp
            LIMIT 5000
        """)

        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()

        if len(rows) < 48:
            raise ValueError(f"Not enough data for forecast (need 48+, got {len(rows)})")

        df = pd.DataFrame(rows)
        df["ds"] = pd.to_datetime(df["ds"])
        if df["ds"].dt.tz is not None:
            df["ds"] = df["ds"].dt.tz_convert("UTC").dt.tz_localize(None)
        df["y"] = pd.to_numeric(df["y"], errors="coerce")
        df = df.dropna().sort_values("ds").drop_duplicates(subset="ds", keep="last")

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            interval_width=0.90,
        )
        import os
        import sys
        with open(os.devnull, "w") as devnull:
            old = sys.stdout
            sys.stdout = devnull
            try:
                model.fit(df)
            finally:
                sys.stdout = old

        # Cache the model for 24h (HMAC-signed so it can't be swapped for a malicious pickle)
        try:
            from core.secure_pickle import dumps_signed
            cache.set(cache_key, dumps_signed(model), ex=86400)
        except Exception:
            pass

    # Generate future dataframe
    future = model.make_future_dataframe(periods=horizon_hours, freq="h")
    forecast = model.predict(future)

    # Only return the future part
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    future_forecast = forecast[forecast["ds"] > now_naive].tail(horizon_hours)

    points = []
    for _, row in future_forecast.iterrows():
        ts = row["ds"].to_pydatetime().replace(tzinfo=timezone.utc)
        points.append(ForecastPoint(
            timestamp=ts,
            value=round(float(row["yhat"]), 4),
            lower=round(float(row["yhat_lower"]), 4),
            upper=round(float(row["yhat_upper"]), 4),
        ))

    return points
