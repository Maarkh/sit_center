# api/limiter.py
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import settings

_storage_uri = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

# Use in-memory storage for testing (when TESTING env var is set)
if os.getenv("TESTING", "").lower() in ("1", "true"):
    _storage_uri = "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri=_storage_uri,
    strategy="fixed-window"
)
