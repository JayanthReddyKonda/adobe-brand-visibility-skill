"""Safe streaming HTTP fetcher using pure standard library urllib.request.

Implements chunked streaming reads with byte caps, custom redirect security validation,
gzip/deflate decompression, and socket latency telemetry.
"""

from __future__ import annotations

import gzip
import ssl
import time
import urllib.error
import urllib.request
import zlib
from typing import Any, Dict, List, Optional

from .budget import Budget, BudgetExhaustedError
from .models import Resource
from .policy import SecurityPolicy, SecurityValidationError


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
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandAuditBot/1.0; +https://agentskills.io/bot)"

    def __init__(
        self,
        policy: Optional[SecurityPolicy] = None,
        budget: Optional[Budget] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.policy = policy or SecurityPolicy()
        self.budget = budget or Budget()
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

        # Build SSL Context with certificate verification
        self.ssl_context = ssl.create_default_context()

    def fetch(
        self,
        url: str,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Resource:
        """Safely fetch an HTTP/HTTPS resource, adhering to security policy and budgets."""
        # Check budget before initiating network call
        self.budget.check_or_raise()

        # Step 1: Pre-validate initial URL
        safe, reason, resolved_ip = self.policy.validate_url(url)
        if not safe:
            raise SecurityValidationError(f"URL pre-validation failed for {url}: {reason}")

        # Compute effective timeout from budget remaining
        budget_remaining = self.budget.remaining_time()
        effective_timeout = min(timeout or 15.0, budget_remaining)
        if effective_timeout <= 0.0:
            raise BudgetExhaustedError("Audit deadline has already expired before fetching.")

        # Prepare request headers with modern Client Hints to avoid false WAF rejections
        req_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, headers=req_headers)

        # Build opener with custom redirect safety handler
        redirect_handler = SafeRedirectHandler(
            policy=self.policy, max_redirects=self.budget.max_redirects
        )
        https_handler = urllib.request.HTTPSHandler(context=self.ssl_context)
        opener = urllib.request.build_opener(redirect_handler, https_handler)

        start_time = time.monotonic()
        try:
            with opener.open(req, timeout=effective_timeout) as resp:
                status_code = resp.getcode()
                final_url = resp.geturl()
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                content_type = resp_headers.get("content-type", "text/html")

                # Stream read body in bounded chunks
                body_chunks: List[bytes] = []
                total_bytes = 0

                while True:
                    # Guard against global deadline during download
                    if self.budget.remaining_time() <= 0.0:
                        raise BudgetExhaustedError("Audit deadline expired during streaming body read.")

                    chunk = resp.read(self.CHUNK_SIZE)
                    if not chunk:
                        break

                    body_chunks.append(chunk)
                    total_bytes += len(chunk)

                    # Update budget telemetry
                    self.budget.record_bytes(len(chunk))

                    # Check single-page limit
                    if total_bytes > self.budget.max_page_bytes:
                        break  # Truncate rather than blowing memory

                raw_body = b"".join(body_chunks)

                # Decompress if required
                decompressed_body = self._decompress_body(raw_body, resp_headers.get("content-encoding"))

                latency_ms = (time.monotonic() - start_time) * 1000.0
                self.budget.record_page()

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
            # Handle transient 429 / 503 with short Retry-After if budget allows
            if e.code in (429, 503) and self.budget.remaining_time() > 10.0:
                retry_header = e.headers.get("retry-after", "") if e.headers else ""
                sleep_sec = 0.0
                if retry_header.isdigit():
                    sleep_sec = min(float(retry_header), 2.0)
                elif retry_header:
                    sleep_sec = 1.0
                if 0.0 < sleep_sec <= 2.0:
                    time.sleep(sleep_sec)
                    try:
                        return self.fetch(url, timeout=timeout, headers=headers)
                    except Exception:
                        pass

            latency_ms = (time.monotonic() - start_time) * 1000.0
            error_body = b""
            try:
                error_body = e.read(self.CHUNK_SIZE)
            except Exception:
                pass

            resp_headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
            return Resource(
                url=url,
                final_url=e.geturl() if hasattr(e, "geturl") else url,
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

    def _decompress_body(self, raw_data: bytes, encoding: Optional[str]) -> bytes:
        """Safely decompress gzip or deflate response payload."""
        if not raw_data or not encoding:
            return raw_data

        enc = encoding.strip().lower()
        if enc == "gzip":
            try:
                return gzip.decompress(raw_data)
            except (gzip.BadGzipFile, zlib.error, EOFError):
                return raw_data
        elif enc == "deflate":
            try:
                return zlib.decompress(raw_data)
            except zlib.error:
                try:
                    # Fallback for raw deflate without zlib headers
                    return zlib.decompress(raw_data, -zlib.MAX_WBITS)
                except zlib.error:
                    return raw_data
        return raw_data
