# core/ssrf.py
# SSRF guard for outbound requests built from user-supplied URLs (data-source
# http_pull, webhook notification channels). Blocks non-http(s) schemes and any URL
# whose host resolves to a private / loopback / link-local / reserved address — so a
# user with write:metrics / write:alerts can't make the server fetch
# http://169.254.169.254/... or http://127.0.0.1:.../ and exfiltrate the response.
import ipaddress
import socket
from urllib.parse import urlparse, urlsplit

ALLOWED_SCHEMES = {"http", "https"}
MAX_REDIRECTS = 3


def _addr_blocked(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    # is_private covers RFC1918 + unique-local IPv6 (fc00::/7); the rest catch
    # loopback, link-local (incl. 169.254/16 cloud metadata), CGNAT, reserved, etc.
    return (
        ip.is_private or ip.is_loopback or ip.is_link_local
        or ip.is_reserved or ip.is_multicast or ip.is_unspecified
    )


def validate_public_url(url: str) -> None:
    """Raise ValueError unless `url` is an http(s) URL whose host resolves only to
    public addresses. Resolves every A/AAAA record and blocks if ANY is internal."""
    parts = urlparse(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme not allowed: {parts.scheme!r}")
    host = parts.hostname
    if not host:
        raise ValueError("URL has no host")
    # A bare IP literal: check it directly (getaddrinfo would echo it back anyway).
    try:
        if _addr_blocked(host):
            raise ValueError(f"host is a blocked address: {host}")
        return  # valid public IP literal
    except ValueError as e:
        if "blocked address" in str(e):
            raise
        # not an IP literal → resolve the hostname
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise ValueError(f"cannot resolve host {host!r}: {e}")
    if not infos:
        raise ValueError(f"cannot resolve host {host!r}")
    for info in infos:
        ip = info[4][0]
        if _addr_blocked(ip):
            raise ValueError(f"host {host!r} resolves to a blocked address: {ip}")


def guarded_request(session_request, method: str, url: str, **kwargs):
    """Perform an outbound request with SSRF protection: validate the URL, disable
    automatic redirects, and re-validate every redirect hop manually. `session_request`
    is a callable like `requests.request` / `requests.Session().request`. Returns the
    final non-redirect response (raises ValueError on a blocked URL)."""
    kwargs["allow_redirects"] = False
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        validate_public_url(current)
        resp = session_request(method, current, **kwargs)
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            if not location:
                return resp
            # resolve relative redirects against the current URL
            current = location if urlsplit(location).netloc else _join(current, location)
            method = "GET" if resp.status_code in (301, 302, 303) else method
            continue
        return resp
    raise ValueError("too many redirects")


def _join(base: str, location: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, location)
