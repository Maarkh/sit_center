# tests/test_mask_secrets_edge.py
"""
Edge-case tests for mask_secrets() — covering formats that reviewers flagged.
"""
from config import mask_secrets


# --- Redis URL edge cases ---

def test_mask_redis_password_only():
    """redis://:password@host (no username)"""
    s = "redis://:SuperSecret123@redis:6379/0"
    out = mask_secrets(s)
    assert "SuperSecret123" not in out
    assert "redis://:***@redis:6379/0" in out


def test_mask_redis_with_username():
    """redis://user:password@host"""
    s = "redis://default:mypass@redis:6379/0"
    out = mask_secrets(s)
    assert "mypass" not in out
    assert "redis://default:***@redis:6379/0" in out


def test_mask_redis_sentinel_url():
    """redis-sentinel://:pass@host"""
    s = "redis://:sentinel_pass@sentinel1:26379/0"
    out = mask_secrets(s)
    assert "sentinel_pass" not in out


def test_mask_redis_empty_password():
    """redis://:@host (empty password) should not crash"""
    s = "redis://:@redis:6379/0"
    out = mask_secrets(s)
    assert "redis://" in out


# --- PostgreSQL URL edge cases ---

def test_mask_postgres_standard():
    s = "postgresql://admin:p4ssw0rd@db:5432/mydb"
    out = mask_secrets(s)
    assert "p4ssw0rd" not in out
    assert "postgresql://admin:***@db:5432/mydb" in out


def test_mask_postgres_special_chars_in_password():
    """Password with special chars: @, :, /, #"""
    s = "postgresql://user:p%40ss%3Aw0rd@db:5432/mydb"
    out = mask_secrets(s)
    assert "p%40ss%3Aw0rd" not in out


def test_mask_postgres_no_username():
    s = "postgres://:secret@db:5432/mydb"
    out = mask_secrets(s)
    assert "secret" not in out


# --- Telegram bot token ---

def test_mask_telegram_token_standard():
    s = "bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz_0123456789"
    out = mask_secrets(s)
    assert "bot123456789:***" in out
    assert "ABCdefGHIjklMNOpqrsTUVwxyz_0123456789" not in out


def test_mask_telegram_token_in_url():
    s = "https://api.telegram.org/bot123456:ABCdef/sendMessage"
    out = mask_secrets(s)
    assert "ABCdef" not in out


# --- JSON key-value pairs ---

def test_mask_json_password():
    s = '{"password": "hunter2"}'
    out = mask_secrets(s)
    assert "hunter2" not in out


def test_mask_json_token():
    s = '{"token": "abc123xyz"}'
    out = mask_secrets(s)
    assert "abc123xyz" not in out


def test_mask_json_secret_key():
    s = "{'secret': 'my_secret_value'}"
    out = mask_secrets(s)
    assert "my_secret_value" not in out


# --- Generic key=value pairs ---

def test_mask_password_equals():
    s = "connection failed password=MySecret123 at host"
    out = mask_secrets(s)
    assert "MySecret123" not in out
    assert "password=***" in out


def test_mask_token_equals():
    s = "token=xoxb-123-456-abc other stuff"
    out = mask_secrets(s)
    assert "xoxb-123-456-abc" not in out


def test_mask_secret_equals():
    s = "SECRET=very_secret_value"
    out = mask_secrets(s)
    assert "very_secret_value" not in out


# --- Edge cases ---

def test_mask_none_input():
    assert mask_secrets(None) == ""


def test_mask_non_string_input():
    result = mask_secrets(12345)
    assert result == "12345"


def test_mask_empty_string():
    assert mask_secrets("") == ""


def test_mask_no_secrets():
    s = "This is a normal log message without any secrets"
    assert mask_secrets(s) == s


def test_mask_multiple_secrets_in_one_string():
    s = "DB: postgresql://user:dbpass@db:5432/mydb Redis: redis://:redispass@redis:6379"
    out = mask_secrets(s)
    assert "dbpass" not in out
    assert "redispass" not in out
    assert "***" in out


def test_mask_preserves_non_secret_content():
    s = "Error connecting to postgresql://admin:secret@db:5432/app — retrying in 5s"
    out = mask_secrets(s)
    assert "secret" not in out
    assert "Error connecting to" in out
    assert "retrying in 5s" in out
