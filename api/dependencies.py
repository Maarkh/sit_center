# api/dependencies.py
from core.metadata_service import metadata_service
from sqlalchemy import create_engine
from config import get_database_url
from api.auth import get_current_user, TokenData
from fastapi import Depends, HTTPException

# Метаданные — синглтон
def get_metadata_service():
    return metadata_service

# БД (если нужно напрямую)
_engine = None
def get_db_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url())
    return _engine

def require_scope(required_scope: str):
    def _check(current_user: TokenData = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return _check