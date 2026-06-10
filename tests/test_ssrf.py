"""SSRF guard (core/ssrf.py) — blocks internal/loopback/link-local + non-http(s)."""
import pytest

from core.ssrf import validate_public_url


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://127.0.0.1:6379/",
    "http://169.254.169.254/latest/meta-data/",   # cloud metadata
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "https://[::1]/",                              # ipv6 loopback
    "http://0.0.0.0/",
    "http://localhost/",                           # resolves to loopback
])
def test_blocks_internal(url):
    with pytest.raises(ValueError):
        validate_public_url(url)


@pytest.mark.parametrize("url", [
    "ftp://example.com/",
    "file:///etc/passwd",
    "gopher://127.0.0.1/",
    "redis://127.0.0.1:6379/",
])
def test_blocks_bad_scheme(url):
    with pytest.raises(ValueError):
        validate_public_url(url)


@pytest.mark.parametrize("url", [
    "http://8.8.8.8/",          # public IP literal — no DNS needed
    "https://1.1.1.1/metrics",
])
def test_allows_public_ip(url):
    validate_public_url(url)  # must not raise


def test_no_host():
    with pytest.raises(ValueError):
        validate_public_url("http:///nohost")
