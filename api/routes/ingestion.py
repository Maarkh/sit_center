# api/routes/ingestion.py
# Authenticated HTTP metric push (M1). External agents POST a batch with the
# X-API-KEY of a registered, enabled http_push data source; the key identifies the
# tenant + source, and the points land in canonical_metrics under them. No JWT — the
# api_key IS the credential (and with no cookie, the CSRF middleware skips it).
from fastapi import APIRouter, HTTPException, Request

from api.schemas import MetricBatchIn
from api.limiter import limiter
from core.data_sources import find_source_by_api_key, insert_metrics
from core.audit import log_audit
from config import logger

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/metrics", summary="Push metrics (X-API-KEY of an http_push source)")
@limiter.limit("1000/minute")
def ingest_metrics(request: Request, batch: MetricBatchIn):
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-KEY header required")
    source = find_source_by_api_key(api_key)
    if not source:
        raise HTTPException(status_code=403, detail="Invalid or disabled API key")
    n = insert_metrics(batch.metrics, source["name"], source["tenant_id"])
    try:
        log_audit(
            f"api_key:{source['name']}", source["tenant_id"], "ingest", "metric",
            changes={"count": n},
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        logger.exception("ingest audit log failed")
    return {"ingested": n}
