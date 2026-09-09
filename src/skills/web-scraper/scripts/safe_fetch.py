"""
safe_fetch.py - Canonical zero-dependency SSRF-safe HTTP/HTTPS fetching utility.
Part of the Brand AI-Readiness multi-skill suite (hosted in web-scraper).

Enforces:
- Strict socket-level zero-trust SSRF IP validation per hop
- RFC-1918, loopback, link-local, carrier-grade NAT, and cloud metadata blocking
- DNS TOCTOU resolution pinning before socket creation
- Bounded decompression (zlib bomb protection) up to MAX_HTML_BYTES (2 MB)
- Max 5 redirects with IP re-validation on every redirect
- Honest, un-spoofed User-Agent with standard HTTP content negotiation headers
"""

import http.client
import ipaddress
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from typing import Any, Dict, List, Optional, Tuple

# Canonical single source of truth for maximum HTML fetch size across all skills (2 MB)
MAX_HTML_BYTES: int = 2 * 1024 * 1024

# Transparent, non-evasive audit user-agent
DEFAULT_USER_AGENT: str = "Brand-AI-Readiness-Audit/1.0.0 (compatible; public audit sensor)"

BLOCKED_NETWORKS: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("100.100.100.200/32"),
    ipaddress.ip_network("169.254.170.2/32"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_safe_host(hostname: Optional[str]) -> Tuple[bool, str, List[Any]]:
    try:
        if not hostname or " " in hostname:
            return False, "Malformed hostname", []

        clean_hostname = (hostname or "").strip().strip("[]")
        result_holder: List[Any] = []
        error_holder: List[Exception] = []

        def _resolve():
            try:
                res = socket.getaddrinfo(clean_hostname, 80, proto=socket.IPPROTO_TCP)
                result_holder.append(res)
            except Exception as e:
                error_holder.append(e)

        t = threading.Thread(target=_resolve, daemon=True)
        t.start()
        t.join(timeout=0.8)
        if t.is_alive():
            return False, "DNS resolution timed out", []
        if error_holder:
            return False, f"DNS resolution failed: {error_holder[0]}", []
        if not result_holder:
            return False, "No IP resolved", []
        ip_info = result_holder[0]

        safe_ips = []
        for sf in ip_info:
            ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address = ipaddress.ip_address(sf[4][0])
            if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None:
                ip_obj = ip_obj.ipv4_mapped
            is_blocked = False
            if (
                ip_obj.is_multicast
                or getattr(ip_obj, "is_reserved", False)
                or ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
            ):
                is_blocked = True
            for blocked in BLOCKED_NETWORKS:
                if ip_obj in blocked:
                    is_blocked = True
                    break
            if is_blocked:
                return False, f"IP {sf[4][0]} is in blocked network", []
            safe_ips.append(sf)

        if not safe_ips:
            return False, "No valid public IPs resolved", []

        return True, "", safe_ips
    except Exception as e:
        return False, f"DNS resolution failed: {e}", []


class SafeHTTPConnection(http.client.HTTPConnection):
    def connect(self) -> None:
        is_safe, err, safe_ips = _is_safe_host(self.host)
        if not is_safe:
            raise urllib.error.URLError(f"SSRF blocked: {err}")
        source_addr = getattr(self, "source_address", None)
        self.sock = socket.create_connection((safe_ips[0][4][0], self.port), self.timeout, source_addr)


class SafeHTTPSConnection(http.client.HTTPSConnection):
    def connect(self) -> None:
        is_safe, err, safe_ips = _is_safe_host(self.host)
        if not is_safe:
            raise urllib.error.URLError(f"SSRF blocked: {err}")
        source_addr = getattr(self, "source_address", None)
        self.sock = socket.create_connection((safe_ips[0][4][0], self.port), self.timeout, source_addr)
        if getattr(self, "_tunnel_host", None):
            tunnel_fn = getattr(self, "_tunnel", None)
            if callable(tunnel_fn):
                tunnel_fn()
        context = getattr(self, "_context", None) or ssl.create_default_context()
        self.sock = context.wrap_socket(self.sock, server_hostname=self.host)


class SafeHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(SafeHTTPConnection, req)


class SafeHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(SafeHTTPSConnection, req, context=ssl.create_default_context())


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, max_redirects: int = 5) -> None:
        self.max_redirects = max_redirects
        self.redirects = 0

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Optional[urllib.request.Request]:
        self.redirects += 1
        if self.redirects > self.max_redirects:
            raise urllib.error.URLError("Too many redirects")
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme not in ("http", "https"):
            raise urllib.error.URLError(f"Disallowed redirect scheme: {parsed.scheme}")

        is_safe, err, _ = _is_safe_host(parsed.hostname)
        if not is_safe:
            raise urllib.error.URLError(f"SSRF blocked on redirect: {err}")

        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _decompress_bounded(response: Any, max_bytes: int) -> bytes:
    encoding = response.headers.get("Content-Encoding", "").lower()
    if encoding == "gzip":
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    elif encoding == "deflate":
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    elif encoding in ("zstd", "br"):
        raise ValueError(f"Unsupported encoding: {encoding}")
    else:
        return response.read(max_bytes)

    out = bytearray()
    while len(out) < max_bytes:
        chunk = response.read(8192)
        if not chunk:
            break
        try:
            remaining = max_bytes - len(out)
            decompressed = decompressor.decompress(chunk, max_length=remaining)
            out.extend(decompressed)
            if decompressor.unconsumed_tail or len(out) >= max_bytes:
                return bytes(out[:max_bytes])
        except Exception as e:
            raise ValueError(f"Decompression error: {e}") from e
    return bytes(out)


def safe_fetch(
    url: str,
    timeout: float = 10.0,
    max_bytes: int = MAX_HTML_BYTES,
    user_agent: Optional[str] = None,
    method: str = "GET",
    deadline: Optional[float] = None,
    is_retry: bool = False,
) -> Tuple[Optional[int], str, Dict[str, str], str]:
    """Fetch URL with strict SSRF controls, size limits, and non-evasive headers.

    Returns:
        (status_code, response_body_text, response_headers_dict, error_message)
    """
    if deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0.1:
            return None, "", {}, "Global deadline exceeded"
        timeout = min(timeout, remaining)

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None, "", {}, f"Disallowed scheme: {parsed.scheme}"
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        return None, "", {}, "Malformed URL: credentials and missing host are disallowed"
    if max_bytes < 0:
        return None, "", {}, "Invalid max_bytes: must be non-negative"

    opener = urllib.request.build_opener(
        SafeHTTPHandler(),
        SafeHTTPSHandler(),
        SafeRedirectHandler(max_redirects=5),
    )

    ua = user_agent if user_agent else DEFAULT_USER_AGENT
    # Standard HTTP content negotiation headers (no browser/OS spoofing)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    }
    req = urllib.request.Request(url, headers=headers, method=method)

    try:
        with opener.open(req, timeout=timeout) as response:
            status = response.status
            resp_headers = {k.lower(): v for k, v in response.getheaders()}

            if method == "HEAD":
                return status, "", resp_headers, ""

            try:
                content = _decompress_bounded(response, max_bytes)
            except ValueError as e:
                return status, "", resp_headers, str(e)

            # Multi-stage encoding with BOM stripping
            if content.startswith(b"\xef\xbb\xbf"):
                content = content[3:]
            elif content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
                content = content[2:]

            charset = response.headers.get_content_charset()
            if charset:
                try:
                    html = content.decode(charset, errors="replace")
                except Exception:
                    html = content.decode("utf-8", errors="replace")
            else:
                try:
                    html = content.decode("utf-8")
                except UnicodeDecodeError:
                    html = content.decode("latin-1")
            html = html.replace("\ufeff", "")

            return status, html, resp_headers, ""
    except urllib.error.HTTPError as e:
        if e.code in (429, 503) and not is_retry:
            retry_header = e.headers.get("retry-after", "") if e.headers else ""
            sleep_sec = 0.0
            if retry_header.isdigit():
                sleep_sec = min(float(retry_header), 2.0)
            elif retry_header:
                sleep_sec = 1.0
            if 0.0 < sleep_sec <= 2.0:
                time.sleep(sleep_sec)
                return safe_fetch(
                    url,
                    timeout=timeout,
                    max_bytes=max_bytes,
                    user_agent=user_agent,
                    method=method,
                    deadline=deadline,
                    is_retry=True,
                )
        return e.code, "", {k.lower(): v for k, v in e.headers.items()} if e.headers else {}, str(e)
    except Exception as e:
        return None, "", {}, str(e)


def safe_check_status(url: str, timeout: float = 5.0, deadline: Optional[float] = None) -> Optional[int]:
    """Lightweight check to probe status code without downloading full response."""
    status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=1024, method="HEAD", deadline=deadline)
    if status in (403, 405, 501):
        status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=1024, method="GET", deadline=deadline)
    return status


__all__ = [
    "MAX_HTML_BYTES",
    "DEFAULT_USER_AGENT",
    "BLOCKED_NETWORKS",
    "safe_fetch",
    "safe_check_status",
    "SafeHTTPConnection",
    "SafeHTTPSConnection",
    "SafeHTTPHandler",
    "SafeHTTPSHandler",
    "SafeRedirectHandler",
    "_is_safe_host",
    "_decompress_bounded",
]
