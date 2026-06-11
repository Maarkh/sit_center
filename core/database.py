# core/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, Session
from config import settings, get_database_url
import logging
import threading
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("db")

_engine = None
_engine_lock = threading.Lock()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OperationalError)
)
def get_engine():
    global _engine

    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        database_url = str(get_database_url())

        pool_size = getattr(settings, "DB_POOL_SIZE", 20)
        max_overflow = getattr(settings, "DB_MAX_OVERFLOW", 40)

        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "options": "-c statement_timeout=30000",
                "connect_timeout": 10,
            }
        )

        # RLS request-context hooks: push the per-request tenant onto each pooled
        # connection so DB-level row security can enforce tenant isolation (fail-open
        # when no request context is set — workers/migrations are unaffected).
        try:
            from core.rls import install_rls, warn_if_rls_bypassed
            install_rls(_engine)
            warn_if_rls_bypassed(_engine)
        except Exception as e:
            logger.warning(f"RLS hooks not installed: {e}")

        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info(f"SQLAlchemy engine initialized (pool_size={pool_size}, max_overflow={max_overflow})")

    return _engine


def get_session() -> Session:
    """Return a new SQLAlchemy Session bound to the shared engine.

    The engine is resolved per call via get_engine() (not bound at import), so
    code/tests that patch core.database.get_engine still bind to the right engine.
    Prefer this over rebuilding `sessionmaker(bind=...)` inline at each call site.
    """
    return sessionmaker(bind=get_engine())()


def get_db():
    """FastAPI dependency: yields a request-scoped Session and always closes it.

        @router.get(...)
        def handler(db: Session = Depends(get_db)): ...
    """
    db = get_session()
    try:
        yield db
    finally:
        db.close()
