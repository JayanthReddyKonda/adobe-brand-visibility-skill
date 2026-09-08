"""URL normalization, link extraction, and origin filtering for web acquisition.

Handles canonical URL normalization, fragment stripping, asset extension filtering,
and same-origin classification.
Pure Python standard library (urllib.parse, os.path).
"""

from __future__ import annotations

import os
import re
from typing import List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

from .models import Link

# Static non-HTML assets that should not be queued for HTML crawling
IGNORED_EXTENSIONS: Set[str] = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".css",
    ".js",
    ".mjs",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".mp4",
    ".webm",
    ".avi",
    ".mov",
    ".mp3",
    ".wav",
    ".ogg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".xml",
    ".json",
    ".txt",
    ".csv",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}

NON_HTTP_SCHEMES: Set[str] = {"mailto", "tel", "javascript", "data", "whatsapp", "sms"}


TRACKING_PARAMS: Set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "_hsenc",
    "_hsmi",
    "hsCtaTracking",
    "session_id",
    "sid",
}

JUNK_PATH_PATTERNS: Tuple[str, ...] = (
    r"^/wp-(?:admin|login|json)",
    r"^/(?:cart|checkout|basket)/?",
    r"^/(?:login|signin|sign-in|signup|sign-up|register|logout|auth)/?",
    r"^/(?:my-account|profile|account|wishlist|orders)/?",
    r"^/(?:search|find)/?",
    r"/page/\d+/?$",
    r"/p/\d+/?$",
)

UNSAFE_PATH_REGEX = re.compile(
    r'(?i)(?:^|[/_.?&=+-])(logout|login|signin|signout|checkout|cart|basket|purchase|buy|delete|remove|unsubscribe|subscribe|confirm|activate|reset|admin|account|oauth|token|session|password|payment|action|download)(?:$|[/_.?&=+-])'
)


class LinkProcessor:
    """Provides canonicalization, extraction, and validation of links."""

    @staticmethod
    def normalize_url(url: str) -> Optional[str]:
        """Normalizes a URL by lowercasing scheme/host, removing fragments, tracking parameters, and default ports."""
        if not url or not url.strip():
            return None

        clean_url, _ = urldefrag(url.strip())
        try:
            parsed = urlparse(clean_url)
        except Exception:
            return None

        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            return None

        host = parsed.hostname
        if not host:
            return None
        host = host.lower()

        # Strip standard ports
        port = parsed.port
        netloc = host
        if port and not (scheme == "http" and port == 80) and not (scheme == "https" and port == 443):
            netloc = f"{host}:{port}"

        # Clean path: empty becomes "/"
        path = parsed.path or "/"
        # Resolve redundant slashes in path
        while "//" in path:
            path = path.replace("//", "/")

        # Strip tracking query parameters
        clean_query = ""
        if parsed.query:
            from urllib.parse import parse_qsl, urlencode

            q_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            kept_pairs = [(k, v) for k, v in q_pairs if k.lower() not in TRACKING_PARAMS]
            if kept_pairs:
                clean_query = urlencode(kept_pairs)

        return urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))

    @staticmethod
    def is_same_origin(base_url: str, target_url: str, allow_subdomains: bool = False) -> bool:
        """Determines if target_url belongs to the same domain as base_url."""
        try:
            base_p = urlparse(base_url)
            target_p = urlparse(target_url)
        except Exception:
            return False

        base_host = (base_p.hostname or "").lower()
        target_host = (target_p.hostname or "").lower()

        if not base_host or not target_host:
            return False

        if base_host == target_host:
            return True

        if allow_subdomains:
            # Check if target is subdomain of base (e.g. docs.example.com vs example.com)
            if target_host.endswith("." + base_host):
                return True
            # Check if base is www.example.com and target is example.com
            if base_host.startswith("www.") and base_host[4:] == target_host:
                return True
            if target_host.startswith("www.") and target_host[4:] == base_host:
                return True

        return False

    @classmethod
    def is_crawlable_html_url(cls, url: str) -> bool:
        """Checks if URL is a substantive HTML page rather than an asset, utility route, or unsafe mutation endpoint."""
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        if parsed.scheme.lower() in NON_HTTP_SCHEMES:
            return False

        path = parsed.path.lower()
        _, ext = os.path.splitext(path)
        if ext in IGNORED_EXTENSIONS:
            return False

        # Filter out unsafe / destructive routes (action=delete, logout, etc.)
        from urllib.parse import unquote
        full_query = parsed.path + ("?" + parsed.query if parsed.query else "")
        if UNSAFE_PATH_REGEX.search(unquote(full_query)):
            return False

        # Filter out junk utility routes (cart, checkout, login, pagination)
        return all(not re.search(pattern, path) for pattern in JUNK_PATH_PATTERNS)

    @classmethod
    def resolve_and_filter_links(
        cls,
        base_url: str,
        raw_links: List[Tuple[str, str, Optional[str]]],
        allow_subdomains: bool = False,
    ) -> List[Link]:
        """Resolves raw (href, text, rel) tuples against base_url and discards invalid links."""
        results: List[Link] = []
        seen: Set[str] = set()

        for href, text, rel in raw_links:
            if not href or href.strip().startswith("#"):
                continue

            full_url = urljoin(base_url, href.strip())
            norm_url = cls.normalize_url(full_url)
            if not norm_url or norm_url in seen:
                continue

            seen.add(norm_url)
            is_internal = cls.is_same_origin(base_url, norm_url, allow_subdomains=allow_subdomains)
            results.append(
                Link(
                    href=norm_url,
                    text=text.strip(),
                    rel=rel,
                    is_internal=is_internal,
                )
            )

        return results


def safe_path(url: str) -> bool:
    """Check if URL contains unsafe or mutating query paths."""
    from urllib.parse import unquote, urlsplit

    p = urlsplit(url)
    full = unquote(p.path + ("?" + p.query if p.query else ""))
    return not bool(UNSAFE_PATH_REGEX.search(full))


def normalize(url: str) -> str:
    """Normalize public HTTP/HTTPS URL per strict safety contract."""
    from urllib.parse import quote, urlsplit, urlunsplit

    if "://" not in url:
        url = "https://" + url
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("Only public unauthenticated HTTP(S) URLs are accepted")
    if p.port not in (None, 80, 443):
        raise ValueError("Nonstandard ports are outside the public-site scope")
    if any(ord(c) < 32 for c in url):
        raise ValueError("Control character in URL")
    host = p.hostname.encode("idna").decode("ascii").lower()
    return urlunsplit((
        p.scheme,
        host + (f":{p.port}" if p.port else ""),
        quote(p.path or "/", safe="/%:@!$&'()*+,;=-._~"),
        quote(p.query, safe="%=&/?@:!$'()*+,;~-._"),
        "",
    ))
