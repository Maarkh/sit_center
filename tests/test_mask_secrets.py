# tests/test_mask_secrets.py
from config import mask_secrets

def test_mask_bot_token():
    s = "token here bot123:ABCdefGHIjkLMNOP12345 rest"
    out = mask_secrets(s)
    assert "bot123:***" in out
    assert "ABCdefGHIjkLMNOP12345" not in out

def test_mask_redis_url():
    s = "redis://user:mysecret@redis:6379/0"
    out = mask_secrets(s)
    assert "redis://user:***@redis:6379/0" in out
    assert "mysecret" not in out
