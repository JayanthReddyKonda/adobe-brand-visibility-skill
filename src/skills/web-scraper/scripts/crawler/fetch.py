"""Safe streaming HTTP fetcher using pure standard library urllib.request.

Implements chunked streaming reads with byte caps, custom redirect security validation,
DNS-pinned sockets to prevent TOCTOU, bounded streaming gzip/deflate decompression,
and socket latency telemetry.
"""

from __future__ import annotations

import email.utils
import http.client
import socket
import ssl
import time
import urllib.error
import urllib.request
import zlib
from typing import Any, Dict, List, Optional

from .budget import Budget, BudgetExhaustedError
from .models import Resource
from .policy import SecurityPolicy, SecurityValidationError


def parse_retry_after(header_val: str) -> float:
    """Parses Retry-After header as integer seconds or RFC 1123 HTTP-date."""
    if not header_val:
        return 0.0
    header_str = header_val.strip()
    if header_str.isdigit():
        return float(header_str)
    try:
        dt = email.utils.parsedate_to_datetime(header_str)
        diff = dt.timestamp() - time.time()
        return max(0.0, diff)
    except Exception:
        return 0.0


class PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection that connects directly to a pre-validated IP address."""

    def __init__(self, host: str, port: Optional[int] = None, timeout: float = 15.0, pinned_ip: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(host, port, timeout=timeout, **kwargs)
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        target_ip = self.pinned_ip or self.host.strip("[]")
        source_addr = getattr(self, "source_address", None)
        self.sock = socket.create_connection((target_ip, self.port), self.timeout, source_addr)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection that connects directly to a pre-validated IP address with TLS SNI verification."""

    def __init__(self, host: str, port: Optional[int] = None, timeout: float = 15.0, pinned_ip: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(host, port, timeout=timeout, **kwargs)
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        target_ip = self.pinned_ip or self.host.strip("[]")
        source_addr = getattr(self, "source_address", None)
        self.sock = socket.create_connection((target_ip, self.port), self.timeout, source_addr)
        if getattr(self, "_tunnel_host", None):
            tunnel_fn = getattr(self, "_tunnel", None)
            if callable(tunnel_fn):
                tunnel_fn()
        server_hostname = self.host.strip("[]")
        ctx = getattr(self, "_context", None) or ssl.create_default_context()
        self.sock = ctx.wrap_socket(self.sock, server_hostname=server_hostname)


class PinnedHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, pinned_ip: Optional[str] = None) -> None:
        super().__init__()
        self.pinned_ip = pinned_ip

    def http_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(
            lambda host, port=None, timeout=15.0, **kwargs: PinnedHTTPConnection(
                host, port, timeout=timeout, pinned_ip=self.pinned_ip, **kwargs
            ),
            req,
        )


class PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, context: ssl.SSLContext, pinned_ip: Optional[str] = None) -> None:
        super().__init__(context=context)
        self.pinned_ip = pinned_ip
        self.ssl_context = context

    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(
            lambda host, port=None, timeout=15.0, **kwargs: PinnedHTTPSConnection(
                host, port, timeout=timeout, pinned_ip=self.pinned_ip, context=self.ssl_context, **kwargs
            ),
            req,
            context=self.ssl_context,
        )


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Intercepts HTTP redirects to enforce SSRF validation and redirect ceilings."""

    def __init__(self, policy: SecurityPolicy, max_redirects: int = 5) -> None:
        super().__init__()
        self.policy = policy
        self.max_redirects = max_redirects
        self.redirect_chain: List[str] = []

    def redirect_request(
        self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Optional[urllib.request.Request]:
        if len(self.redirect_chain) >= self.max_redirects:
            raise SecurityValidationError(f"Exceeded maximum redirects ceiling ({self.max_redirects})")

        original_url = req.full_url
        safe, reason, resolved_url, _ = self.policy.validate_redirect(original_url, newurl)
        if not safe:
            raise SecurityValidationError(f"Redirect security rejection: {reason}")

        self.redirect_chain.append(resolved_url)
        return super().redirect_request(req, fp, code, msg, headers, resolved_url)


class SafeFetcher:
    """Zero-dependency HTTP client configured with security guardrails and budget limits."""

    CHUNK_SIZE = 8192
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandAuditBot/2.1.0; +https://agentskills.io/bot)"

    def __init__(
        self,
        policy: Optional[SecurityPolicy] = None,
        budget: Optional[Budget] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.policy = policy or SecurityPolicy()
        self.budget = budget or Budget()
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.ssl_context = ssl.create_default_context()

    def fetch(
        self,
        url: str,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        max_attempts: int = 2,
    ) -> Resource:
        """Safely fetch an HTTP/HTTPS resource, adhering to security policy and budgets."""
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            # Check budget before initiating network call
            self.budget.check_or_raise()

            # Step 1: Pre-validate initial URL and resolve IP
            safe, reason, resolved_ip = self.policy.validate_url(url)
            if not safe:
                raise SecurityValidationError(f"URL pre-validation failed for {url}: {reason}")

            budget_remaining = self.budget.remaining_time()
            effective_timeout = min(timeout or 15.0, budget_remaining)
            if effective_timeout <= 0.0:
                raise BudgetExhaustedError("Audit deadline has already expired before fetching.")

            req_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
            }
            if headers:
                req_headers.update(headers)

            req = urllib.request.Request(url, headers=req_headers)

            redirect_handler = SafeRedirectHandler(
                policy=self.policy, max_redirects=self.budget.max_redirects
            )
            # Use pinned connection handlers to guarantee DNS TOCTOU protection
            http_handler = PinnedHTTPHandler(pinned_ip=resolved_ip)
            https_handler = PinnedHTTPSHandler(context=self.ssl_context, pinned_ip=resolved_ip)
            opener = urllib.request.build_opener(redirect_handler, http_handler, https_handler)

            start_time = time.monotonic()
            self.budget.record_request()

            try:
                with opener.open(req, timeout=effective_timeout) as resp:
                    status_code = resp.getcode()
                    final_url = resp.geturl()
                    resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                    content_type = resp_headers.get("content-type", "text/html")

                    body_chunks: List[bytes] = []
                    total_bytes = 0

                    while True:
                        if self.budget.remaining_time() <= 0.0:
                            raise BudgetExhaustedError("Audit deadline expired during streaming body read.")

                        chunk = resp.read(self.CHUNK_SIZE)
                        if not chunk:
                            break

                        body_chunks.append(chunk)
                        total_bytes += len(chunk)
                        self.budget.record_bytes(len(chunk))

                        if total_bytes > self.budget.max_page_bytes:
                            break

                    raw_body = b"".join(body_chunks)
                    decompressed_body = self._decompress_body(raw_body, resp_headers.get("content-encoding"))
                    latency_ms = (time.monotonic() - start_time) * 1000.0

                    return Resource(
                        url=url,
                        final_url=final_url,
                        status=status_code,
                        headers=resp_headers,
                        body_bytes=decompressed_body,
                        content_type=content_type,
                        latency_ms=latency_ms,
                        redirects=redirect_handler.redirect_chain,
                        ip_address=resolved_ip,
                    )

            except urllib.error.HTTPError as e:
                # Handle transient 429 / 503 with bounded Retry-After
                if e.code in (429, 503) and attempt < max_attempts and self.budget.remaining_time() > 5.0:
                    retry_header = e.headers.get("retry-after", "") if e.headers else ""
                    wait_sec = min(parse_retry_after(retry_header) or 1.5, 3.0)
                    if 0.0 < wait_sec <= min(3.0, self.budget.remaining_time() - 2.0):
                        time.sleep(wait_sec)
                        continue

                latency_ms = (time.monotonic() - start_time) * 1000.0
                error_body = b""
                try:
                    error_body = e.read(self.CHUNK_SIZE)
                except Exception:
                    pass

                resp_headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
                return Resource(
                    url=url,
                    final_url=getattr(e, "url", getattr(e, "geturl", lambda: url)()),
                    status=e.code,
                    headers=resp_headers,
                    body_bytes=error_body,
                    content_type=resp_headers.get("content-type", "text/html"),
                    latency_ms=latency_ms,
                    redirects=redirect_handler.redirect_chain,
                    ip_address=resolved_ip,
                )

            except urllib.error.URLError as e:
                latency_ms = (time.monotonic() - start_time) * 1000.0
                raise ConnectionError(f"Network transport error for {url}: {e.reason}") from e

        raise ConnectionError(f"Fetch failed for {url} after {max_attempts} attempts.")

    def _decompress_body(self, raw_data: bytes, encoding: Optional[str], max_decoded_bytes: Optional[int] = None) -> bytes:
        """Safely decompress gzip or deflate payload enforcing hard decoded byte limit."""
        if not raw_data or not encoding:
            return raw_data

        limit = max_decoded_bytes or (self.budget.max_page_bytes * 2)
        enc = encoding.strip().lower()

        if enc in ("gzip", "deflate"):
            wbits = (16 + zlib.MAX_WBITS) if enc == "gzip" else zlib.MAX_WBITS
            try:
                dobj = zlib.decompressobj(wbits)
                decompressed_chunks: List[bytes] = []
                total_len = 0
                chunk_len = 16384
                for i in range(0, len(raw_data), chunk_len):
                    chunk = dobj.decompress(raw_data[i:i + chunk_len])
                    decompressed_chunks.append(chunk)
                    total_len += len(chunk)
                    if total_len >= limit:
                        break
                if total_len < limit:
                    decompressed_chunks.append(dobj.flush())
                return b"".join(decompressed_chunks)[:limit]
            except zlib.error:
                if enc == "deflate":
                    try:
                        # Raw deflate fallback without zlib wrapper
                        dobj = zlib.decompressobj(-zlib.MAX_WBITS)
                        return dobj.decompress(raw_data)[:limit]
                    except zlib.error:
                        return raw_data
                return raw_data
        return raw_data
