# config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
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
        # Correlation fields injected by middleware
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_entry["tenant_id"] = record.tenant_id
        if record.exc_info:
            tb = self.formatException(record.exc_info)
            log_entry["exception"] = mask_secrets(tb)
        return json.dumps(log_entry, ensure_ascii=False)

class Settings(BaseSettings):
    # --- Подключение к БД ---
    DATABASE_URL: Optional[PostgresDsn] = Field(None) # type: ignore
    POSTGRES_USER: str = Field(...) # type: ignore
    POSTGRES_PASSWORD: str = Field(...) # type: ignore
    POSTGRES_SERVER: str = Field(...) # type: ignore
    POSTGRES_PORT: int = Field(...) # type: ignore
    POSTGRES_DB: str = Field(...) # type: ignore

    # --- Redis ---
    REDIS_HOST: str = Field(...) # type: ignore
    REDIS_PORT: int = Field(...) # type: ignore
    REDIS_DB: int = Field(0) # type: ignore
    REDIS_PASSWORD: Optional[str] = Field(None) # type: ignore
    REDIS_URL: Optional[str] = Field(None) # type: ignore
    # --- Redis Sentinel (HA). When REDIS_SENTINELS is set, clients discover the
    # current master via Sentinel instead of connecting to REDIS_HOST directly.
    # Format: "host1:26379,host2:26379,host3:26379".
    REDIS_SENTINELS: Optional[str] = Field(None)  # type: ignore
    REDIS_MASTER_NAME: str = Field("mymaster")  # type: ignore
    REDIS_SENTINEL_PASSWORD: Optional[str] = Field(None)  # type: ignore

    # --- Пути ---
    data_regions_path: Path = PROJECT_ROOT / "data" / "regions.csv"
    geojson_path: Path = PROJECT_ROOT / "data" / "russia.geojson"
    static_folder: Path = PROJECT_ROOT / "static"
    log_dir: Path = PROJECT_ROOT / "logs"

    # --- Аудио ---
    audio_file_path: str = "alert.mp3"

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None) # type: ignore
    TELEGRAM_CHAT_ID: Optional[str] = Field(None) # type: ignore
    TELEGRAM_CHAT_ID_WARNING: Optional[str] = Field(None) # type: ignore
    TELEGRAM_CHAT_ID_CRITICAL: Optional[str] = Field(None) # type: ignore

    # --- Кэширование ---
    cache_ttl: int = 30  # секунд
    smart_alert_cache_ttl: int = 300  # 5 минут
    cache_locking_timeout: int = 30  # seconds
    cache_poll_interval: float = 0.1  # seconds

    # --- Логирование ---
    log_level: str = "INFO"
    
    # ML настройки
    ml_model_cache_days: int = Field(7) # type: ignore
    ml_retrain_hour: int = Field(3) # type: ignore
    ml_methods: List[str] = Field(["prophet", "lstm", "clustering"]) # type: ignore
    ML_MAX_WORKERS: int = Field(4)  # type: ignore # Количество параллельных воркеров

    # --- Ключи кэша ---
    GEOJSON_CACHE_KEY: str = "geojson_data"
    DASHBOARD_CACHE_KEY: str = "custom_dashboard_metrics"

    # --- Прочее ---
    secret_key: str = Field(...) # type: ignore
    alert_cooldown: int = 3600  # секунд
    
    I_DOIT_API_KEY: str = Field(...) # type: ignore
    I_DOIT_API_URL: str = Field(...) # type: ignore
    ADMIN_USERNAME: str = Field(...) # type: ignore
    ADMIN_PASSWORD: str = Field(...)     # type: ignore
    WEBHOOK_API_KEY: str = Field(...) # type: ignore

    # --- Auth bootstrap ---
    # Env-admin fallback on /token (ADMIN_USERNAME/ADMIN_PASSWORD → full admin). Needed
    # to bootstrap the first admin / for the local demo; set ENV_ADMIN_ENABLED=false in
    # production once a real DB admin exists — it is a standing cross-tenant superuser.
    ENV_ADMIN_ENABLED: bool = Field(True) # type: ignore

    # --- Kafka ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field("kafka:9092") # type: ignore
    KAFKA_ENABLED: bool = Field(False) # type: ignore

    # --- ClickHouse ---
    CLICKHOUSE_HOST: str = Field("clickhouse") # type: ignore
    CLICKHOUSE_PORT: int = Field(8123) # type: ignore
    CLICKHOUSE_USER: str = Field("default") # type: ignore
    CLICKHOUSE_PASSWORD: str = Field("") # type: ignore
    CLICKHOUSE_DB: str = Field("sit_center") # type: ignore
    CLICKHOUSE_ENABLED: bool = Field(False) # type: ignore

    # --- LDAP ---
    LDAP_ENABLED: bool = Field(False) # type: ignore
    LDAP_URL: str = Field("ldap://localhost:389") # type: ignore
    LDAP_BASE_DN: str = Field("") # type: ignore
    LDAP_BIND_DN: str = Field("") # type: ignore
    LDAP_BIND_PASSWORD: str = Field("") # type: ignore
    LDAP_USER_SEARCH_FILTER: str = Field("(sAMAccountName={username})") # type: ignore
    LDAP_GROUP_ROLE_MAP: Dict[str, str] = Field(default_factory=dict) # type: ignore

    # --- OIDC (Keycloak SSO) ---
    OIDC_ENABLED: bool = Field(False) # type: ignore
    OIDC_ISSUER_URL: str = Field("") # type: ignore
    OIDC_CLIENT_ID: str = Field("") # type: ignore
    OIDC_CLIENT_SECRET: str = Field("") # type: ignore
    OIDC_BASE_URL: str = Field("http://localhost:8000") # type: ignore
    # Claim that carries the user's tenant id (e.g. a Keycloak attribute). Empty → all
    # OIDC users land in 'default'. The value is validated against the tenants table.
    OIDC_TENANT_CLAIM: str = Field("") # type: ignore

    # --- CORS ---
    CORS_ORIGINS: str = Field(
        "http://localhost:8050,http://localhost:3000,http://localhost:8000",
    ) # type: ignore

    # --- Auth cookies ---
    # Secure flag for auth cookies. MUST stay True in production (cookies only
    # over HTTPS). Set COOKIE_SECURE=false for local http dev, or the browser
    # silently drops the cookie.
    COOKIE_SECURE: bool = Field(True)  # type: ignore

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорируем неизвестные поля
    )


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
            if settings.REDIS_SENTINELS:
                # HA: discover the current master through Sentinel.
                from redis.sentinel import Sentinel
                nodes = [(h.split(":")[0], int(h.split(":")[1]))
                         for h in settings.REDIS_SENTINELS.split(",") if h.strip()]
                sentinel = Sentinel(
                    nodes,
                    socket_timeout=5,
                    sentinel_kwargs=({"password": settings.REDIS_SENTINEL_PASSWORD}
                                     if settings.REDIS_SENTINEL_PASSWORD else None),
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                )
                _redis_client = sentinel.master_for(
                    settings.REDIS_MASTER_NAME,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
            elif settings.REDIS_URL:
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
    
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    if log_format == "text":
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        formatter = JsonFormatter()

    # Attach request_id filter (injected by middleware)
    try:
        from api.middleware import RequestIdFilter
        logger.addFilter(RequestIdFilter())
    except ImportError:
        pass

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