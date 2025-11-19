# core/exceptions.py
"""
Иерархия исключений для Situational Center

✅ Преимущества:
- Специфичная обработка ошибок
- Улучшенное логирование
- Правильные HTTP статусы
- Контекст для debugging
"""

from typing import Optional, Dict, Any


class SituationalCenterError(Exception):
    """Базовое исключение проекта"""
    
    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для API ответов"""
        return {
            "error": self.code,
            "message": self.message,
            "context": self.context
        }


# === Database Errors ===

class DatabaseError(SituationalCenterError):
    """Ошибки работы с БД"""
    pass


class DuplicateAlertError(DatabaseError):
    """Попытка создать дубликат алерта"""
    
    def __init__(self, fingerprint: str, existing_id: Optional[str] = None):
        super().__init__(
            f"Alert with fingerprint {fingerprint} already exists",
            code="DUPLICATE_ALERT",
            context={"fingerprint": fingerprint, "existing_id": existing_id}
        )
        self.fingerprint = fingerprint
        self.existing_id = existing_id


class DatabaseUnavailableError(DatabaseError):
    """БД временно недоступна"""
    
    def __init__(self, original_error: Exception):
        super().__init__(
            "Database temporarily unavailable",
            code="DB_UNAVAILABLE",
            context={"original_error": str(original_error)}
        )
        self.original_error = original_error


class QueryTimeoutError(DatabaseError):
    """Таймаут выполнения запроса"""
    
    def __init__(self, query: str, timeout_seconds: int):
        super().__init__(
            f"Query timed out after {timeout_seconds}s",
            code="QUERY_TIMEOUT",
            context={"query": query[:100], "timeout": timeout_seconds}
        )


# === Cache Errors ===

class CacheError(SituationalCenterError):
    """Ошибки работы с кэшем (Redis)"""
    pass


class CacheConnectionError(CacheError):
    """Не удалось подключиться к Redis"""
    
    def __init__(self, host: str, port: int):
        super().__init__(
            f"Failed to connect to Redis at {host}:{port}",
            code="CACHE_CONNECTION_ERROR",
            context={"host": host, "port": port}
        )


class CacheLockTimeoutError(CacheError):
    """Таймаут получения distributed lock"""
    
    def __init__(self, lock_name: str, timeout: float):
        super().__init__(
            f"Failed to acquire lock '{lock_name}' within {timeout}s",
            code="LOCK_TIMEOUT",
            context={"lock_name": lock_name, "timeout": timeout}
        )


# === ML Errors ===

class MLModelError(SituationalCenterError):
    """Ошибки ML-моделей"""
    pass


class ModelTrainingError(MLModelError):
    """Ошибка обучения модели"""
    
    def __init__(
        self,
        metric_name: str,
        method: str,
        reason: str
    ):
        super().__init__(
            f"Failed to train {method} model for {metric_name}: {reason}",
            code="MODEL_TRAINING_ERROR",
            context={"metric": metric_name, "method": method, "reason": reason}
        )


class InsufficientDataError(MLModelError):
    """Недостаточно данных для обучения"""
    
    def __init__(self, metric_name: str, required: int, actual: int):
        super().__init__(
            f"Insufficient data for {metric_name}: need {required}, got {actual}",
            code="INSUFFICIENT_DATA",
            context={"metric": metric_name, "required": required, "actual": actual}
        )


class ModelNotFoundError(MLModelError):
    """Модель не найдена в кэше"""
    
    def __init__(self, metric_name: str, region: str):
        super().__init__(
            f"No trained model for {metric_name} in {region}",
            code="MODEL_NOT_FOUND",
            context={"metric": metric_name, "region": region}
        )


# === Alert Errors ===

class AlertError(SituationalCenterError):
    """Ошибки системы алертов"""
    pass


class AlertSendError(AlertError):
    """Не удалось отправить уведомление"""
    
    def __init__(self, channel: str, reason: str):
        super().__init__(
            f"Failed to send alert via {channel}: {reason}",
            code="ALERT_SEND_ERROR",
            context={"channel": channel, "reason": reason}
        )


class RateLimitExceededError(AlertError):
    """Превышен лимит отправки алертов"""
    
    def __init__(self, limit: int, window: int):
        super().__init__(
            f"Rate limit exceeded: {limit} alerts per {window}s",
            code="RATE_LIMIT_EXCEEDED",
            context={"limit": limit, "window": window}
        )


# === Configuration Errors ===

class ConfigurationError(SituationalCenterError):
    """Ошибки конфигурации"""
    pass


class MetricNotFoundError(ConfigurationError):
    """Метрика не найдена в metadata"""
    
    def __init__(self, metric_name: str):
        super().__init__(
            f"Metric '{metric_name}' not found or inactive",
            code="METRIC_NOT_FOUND",
            context={"metric_name": metric_name}
        )


class InvalidDimensionError(ConfigurationError):
    """Недопустимое измерение"""
    
    def __init__(self, dimension: str, allowed: list):
        super().__init__(
            f"Dimension '{dimension}' not allowed. Allowed: {allowed}",
            code="INVALID_DIMENSION",
            context={"dimension": dimension, "allowed": allowed}
        )


# === Validation Errors ===

class ValidationError(SituationalCenterError):
    """Ошибки валидации данных"""
    pass


class TimeRangeError(ValidationError):
    """Неверный временной диапазон"""
    
    def __init__(self, reason: str):
        super().__init__(
            f"Invalid time range: {reason}",
            code="TIME_RANGE_ERROR",
            context={"reason": reason}
        )


class InputSizeLimitError(ValidationError):
    """Превышен лимит размера входных данных"""
    
    def __init__(self, input_type: str, limit: int, actual: int):
        super().__init__(
            f"{input_type} size {actual} exceeds limit {limit}",
            code="INPUT_SIZE_LIMIT",
            context={"type": input_type, "limit": limit, "actual": actual}
        )

class InvalidDimensionKeyError(ConfigurationError):
    """Недопустимый ключ измерения (попытка инъекции)"""
    def __init__(self, key: str):
        super().__init__(
            f"Invalid dimension key: '{key}'. Must match ^[a-zA-Z0-9_\-]{{1,50}}$", # type: ignore
            code="INVALID_DIMENSION_KEY",
            context={"key": key}
        )

# === API Error Handlers ===
# Используйте в api/main.py

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, DatabaseError as SQLADatabaseError
import logging

logger = logging.getLogger(__name__)


async def situational_center_error_handler(
    request: Request,
    exc: SituationalCenterError
) -> JSONResponse:
    """Обработчик всех кастомных исключений"""
    
    # Определяем HTTP статус по типу ошибки
    status_codes = {
        DatabaseUnavailableError: 503,
        QueryTimeoutError: 504,
        CacheConnectionError: 503,
        CacheLockTimeoutError: 408,
        DuplicateAlertError: 409,
        MetricNotFoundError: 404,
        ModelNotFoundError: 404,
        ValidationError: 400,
        InvalidDimensionError: 400,
        TimeRangeError: 400,
        InputSizeLimitError: 413,
        RateLimitExceededError: 429,
        AlertSendError: 502,
        ModelTrainingError: 500,
        InsufficientDataError: 400,
    }
    
    status_code = status_codes.get(type(exc), 500)
    
    # Логируем в зависимости от severity
    if status_code >= 500:
        logger.error(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"context": exc.context, "request_path": request.url.path}
        )
    else:
        logger.warning(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"context": exc.context}
        )
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLADatabaseError
) -> JSONResponse:
    """Обработчик ошибок SQLAlchemy"""
    
    # Конвертируем в наши исключения
    if isinstance(exc, IntegrityError):
        logger.warning(f"Integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content={
                "error": "CONFLICT",
                "message": "Data conflict (duplicate or constraint violation)"
            }
        )
    
    if isinstance(exc, OperationalError):
        logger.error(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "DB_UNAVAILABLE",
                "message": "Database temporarily unavailable"
            }
        )
    
    # Общая ошибка БД
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "DB_ERROR",
            "message": "Database error occurred"
        }
    )
    
