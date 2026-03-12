# config.py
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict
from pydantic import Field, PostgresDsn
import logging
import logging.handlers
import redis
import json
import os
import re
import threading

# Создаём базовый логгер сразу
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sit_center")

PROJECT_ROOT = Path(__file__).parent

def mask_secrets(s: str) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)

    # Redis/Postgres URLs: mask password between : and @
    s = re.sub(r"(redis://[^:@]*:)([^@]+)(@)", r"\1***\3", s, flags=re.IGNORECASE)
    s = re.sub(r"(postgres(?:ql)?://[^:@]*:)([^@]+)(@)", r"\1***\3", s, flags=re.IGNORECASE)

    # Telegram bot token: bot<id>:<token> -> bot<id>:***
    s = re.sub(r"(bot\d+:)[A-Za-z0-9_\-]+", r"\1***", s, flags=re.IGNORECASE)

    # JSON keys like "password": "xxx" -> mask value
    s = re.sub(
        r'(["\'])(password|token|secret|key|pwd|pass)(["\']\s*:\s*["\'])([^"\']+)(["\'])',
        r'\1\2\3***\5',
        s,
        flags=re.IGNORECASE
    )

    # Generic key=value pairs
    s = re.sub(r'\b(password|pwd|secret|token)=\S+', r'\1=***', s, flags=re.IGNORECASE)

    return s

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_secrets(record.getMessage()),
        }
        if record.exc_info:
            # Маскируем traceback тоже
            tb = self.formatException(record.exc_info)
            log_entry["exception"] = mask_secrets(tb)
        return json.dumps(log_entry, ensure_ascii=False)

class Settings(BaseSettings):
    # --- Подключение к БД ---
    DATABASE_URL: Optional[PostgresDsn] = Field(None, env="DATABASE_URL") # type: ignore
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER") # type: ignore
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD") # type: ignore
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER") # type: ignore
    POSTGRES_PORT: int = Field(..., env="POSTGRES_PORT") # type: ignore
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB") # type: ignore

    # --- Redis ---
    REDIS_HOST: str = Field(..., env="REDIS_HOST") # type: ignore
    REDIS_PORT: int = Field(..., env="REDIS_PORT") # type: ignore
    REDIS_DB: int = Field(0, env="REDIS_DB") # type: ignore
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD") # type: ignore
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL") # type: ignore

    # --- Пути ---
    data_regions_path: Path = PROJECT_ROOT / "data" / "regions.csv"
    geojson_path: Path = PROJECT_ROOT / "data" / "russia.geojson"
    static_folder: Path = PROJECT_ROOT / "static"
    log_dir: Path = PROJECT_ROOT / "logs"

    # --- Аудио ---
    audio_file_path: str = "alert.mp3"

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN") # type: ignore
    TELEGRAM_CHAT_ID: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID") # type: ignore
    TELEGRAM_CHAT_ID_WARNING: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID_WARNING") # type: ignore
    TELEGRAM_CHAT_ID_CRITICAL: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID_CRITICAL") # type: ignore

    # --- Кэширование ---
    cache_ttl: int = 30  # секунд
    smart_alert_cache_ttl: int = 300  # 5 минут
    cache_locking_timeout: int = 30  # seconds
    cache_poll_interval: float = 0.1  # seconds

    # --- Логирование ---
    log_level: str = "INFO"
    
    # ML настройки
    ml_model_cache_days: int = Field(7, env="ML_MODEL_CACHE_DAYS") # type: ignore
    ml_retrain_hour: int = Field(3, env="ML_RETRAIN_HOUR") # type: ignore
    ml_methods: List[str] = Field(["prophet", "lstm", "clustering"], env="ML_METHODS") # type: ignore
    ML_MAX_WORKERS: int = Field(4, env="ML_MAX_WORKERS")  # type: ignore # Количество параллельных воркеров

    # --- Ключи кэша ---
    GEOJSON_CACHE_KEY: str = "geojson_data"
    DASHBOARD_CACHE_KEY: str = "custom_dashboard_metrics"

    # --- Прочее ---
    secret_key: str = Field(..., env="SECRET_KEY") # type: ignore
    alert_cooldown: int = 3600  # секунд
    
    I_DOIT_API_KEY: str = Field(..., env="I_DOIT_API_KEY") # type: ignore
    I_DOIT_API_URL: str = Field(..., env="I_DOIT_API_URL") # type: ignore
    ADMIN_USERNAME: str = Field(..., env="ADMIN_USERNAME") # type: ignore
    ADMIN_PASSWORD: str = Field(..., env="ADMIN_PASSWORD")     # type: ignore
    WEBHOOK_API_KEY: str = Field(..., env="WEBHOOK_API_KEY") # type: ignore

    # --- Kafka ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field("kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS") # type: ignore
    KAFKA_ENABLED: bool = Field(False, env="KAFKA_ENABLED") # type: ignore

    # --- ClickHouse ---
    CLICKHOUSE_HOST: str = Field("clickhouse", env="CLICKHOUSE_HOST") # type: ignore
    CLICKHOUSE_PORT: int = Field(8123, env="CLICKHOUSE_PORT") # type: ignore
    CLICKHOUSE_USER: str = Field("default", env="CLICKHOUSE_USER") # type: ignore
    CLICKHOUSE_PASSWORD: str = Field("", env="CLICKHOUSE_PASSWORD") # type: ignore
    CLICKHOUSE_DB: str = Field("sit_center", env="CLICKHOUSE_DB") # type: ignore
    CLICKHOUSE_ENABLED: bool = Field(False, env="CLICKHOUSE_ENABLED") # type: ignore

    # --- LDAP ---
    LDAP_ENABLED: bool = Field(False, env="LDAP_ENABLED") # type: ignore
    LDAP_URL: str = Field("ldap://localhost:389", env="LDAP_URL") # type: ignore
    LDAP_BASE_DN: str = Field("", env="LDAP_BASE_DN") # type: ignore
    LDAP_BIND_DN: str = Field("", env="LDAP_BIND_DN") # type: ignore
    LDAP_BIND_PASSWORD: str = Field("", env="LDAP_BIND_PASSWORD") # type: ignore
    LDAP_USER_SEARCH_FILTER: str = Field("(sAMAccountName={username})", env="LDAP_USER_SEARCH_FILTER") # type: ignore
    LDAP_GROUP_ROLE_MAP: Dict[str, str] = Field(default_factory=dict, env="LDAP_GROUP_ROLE_MAP") # type: ignore

    # --- OIDC (Keycloak SSO) ---
    OIDC_ENABLED: bool = Field(False, env="OIDC_ENABLED") # type: ignore
    OIDC_ISSUER_URL: str = Field("", env="OIDC_ISSUER_URL") # type: ignore
    OIDC_CLIENT_ID: str = Field("", env="OIDC_CLIENT_ID") # type: ignore
    OIDC_CLIENT_SECRET: str = Field("", env="OIDC_CLIENT_SECRET") # type: ignore
    OIDC_BASE_URL: str = Field("http://localhost:8000", env="OIDC_BASE_URL") # type: ignore

    # --- CORS ---
    CORS_ORIGINS: str = Field(
        "http://localhost:8050,http://localhost:3000,http://localhost:8000",
        env="CORS_ORIGINS",
    ) # type: ignore

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорируем неизвестные поля


# Inject Vault secrets into env before Settings init (if VAULT_ENABLED=true)
try:
    from core.vault import inject_vault_secrets
    inject_vault_secrets()
except Exception:
    pass

settings = Settings() # type: ignore


# === Глобальные объекты ===

# 🟡 Redis-клиент (ленивая инициализация)
_redis_client = None
_redis_lock = threading.Lock()


def get_redis():
    global _redis_client
    
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError):
            # Соединение потеряно, закрываем старый клиент
            try:
                _redis_client.close()
            except Exception:
                pass
            _redis_client = None
    
    with _redis_lock:
        # Double-check после получения блокировки
        if _redis_client is not None:
            return _redis_client
            
        try:
            if settings.REDIS_URL:
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                _redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            _redis_client.ping()
            logger.info("✅ Подключено к Redis")
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к Redis: {mask_secrets(str(e))}")
            raise
    
    return _redis_client


def close_redis():
    global _redis_client
    with _redis_lock:
        if _redis_client is not None:
            try:
                _redis_client.connection_pool.disconnect()
            except Exception:
                pass
            _redis_client = None

def get_cache():
    """Возвращает Redis-клиент как кэш"""
    return get_redis()


def get_database_url() -> str:
    """Формирует URL для подключения к PostgreSQL"""
    if settings.DATABASE_URL:
        return str(settings.DATABASE_URL)
    return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"


def setup_logging():
    """Инициализация логирования (вызывать после monkey_patch)"""
    global logger
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    settings.log_dir.mkdir(exist_ok=True)
    
    if os.getenv("LOG_JSON", "false").lower() == "true":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        print(f"⚠️ Не удалось создать файл лога: {e}")

    logger.setLevel(settings.log_level.upper())
    logger.info("✅ Логирование инициализировано")
    
def init_app_logging():
    global logger
    try:
        # settings уже инициализирован (Settings())
        logger.handlers.clear()
        logger.setLevel(settings.log_level.upper())
        setup_logging()
    except Exception as e:
        # безопасный fallback
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.warning(f"Не удалось полностью инициализировать логирование: {e}")