"""High-performance Zero-Dependency Web Acquisition Engine and Agent Query API.

Consolidated crawler subsystem combining:
- Data models & acquisition contracts (Resource, Heading, Link, CTA, PageModel, EvidenceModel)
- Zero-Trust SSRF Security Policy & IP pinning (SecurityPolicy, SecurityValidationError)
- Global audit budget & deadline manager (Budget, BudgetExhaustedError)
- Priority URL Frontier & Route Weight Scoring (Frontier, FrontierItem)
- Canonical URL validation (CanonicalValidator)
- Page & Route Archetype Classification (PageClassifier)
- Streaming HTTP Fetcher & Pinned Connections (SafeFetcher, PinnedConnectionPool)
- RFC 9309 Robots.txt Auditor (Robots, RobotsAuditor, RobotsOutcome)
- XML Sitemap Discoverer & Parser (SitemapParser, SitemapDiscovery)
- Single-pass Streaming HTML Parser (StreamingHTMLParser)
- Metadata & Link Processors (MetadataProcessor, LinkProcessor, normalize, safe_path)
- Schema.org JSON-LD Parser & Graph Flattener (JsonLdExtractor)
- Evidence & Clean Markdown Extractor (EvidenceExtractor)
- Master Acquisition Orchestrator (WebAuditEngine)
- Standalone CLI Runner (main)

Pure Python 3.9+ standard library ONLY. Zero runtime third-party pip dependencies.
"""

from __future__ import annotations

import argparse
import email.utils
import heapq
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import quote, unquote, urldefrag, urljoin, urlparse, urlsplit, urlunparse, urlunsplit

# ==============================================================================
# SECTION 1: DATA MODELS & ACQUISITION CONTRACTS
# ==============================================================================


@dataclass
class Resource:
    """Raw HTTP payload container."""

    url: str
    final_url: str
    status: int
    headers: Dict[str, str] = field(default_factory=dict)
    body_bytes: bytes = b""
    content_type: str = "text/html"
    latency_ms: float = 0.0
    redirects: List[str] = field(default_factory=list)
    ip_address: Optional[str] = None
    truncated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary, omitting binary body."""
        return {
            "url": self.url,
            "final_url": self.final_url,
            "status": self.status,
            "headers": self.headers,
            "content_type": self.content_type,
            "latency_ms": round(self.latency_ms, 2),
            "redirects": self.redirects,
            "ip_address": self.ip_address,
            "bytes_length": len(self.body_bytes),
            "truncated": self.truncated,
        }


@dataclass
class Heading:
    """Represents an HTML heading tag (h1-h6)."""

    level: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "text": self.text}


@dataclass
class Link:
    """Represents an extracted hyperlink."""

    href: str
    text: str
    rel: Optional[str] = None
    is_internal: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "href": self.href,
            "text": self.text,
            "rel": self.rel,
            "is_internal": self.is_internal,
        }


@dataclass
class CTA:
    """Represents a call-to-action or interactive action element."""

    text: str
    href: str = ""
    tag: str = "a"
    is_commercial_cta: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "href": self.href,
            "tag": self.tag,
            "is_commercial_cta": self.is_commercial_cta,
        }


@dataclass
class HreflangLink:
    """Represents an internationalization hreflang alternate declaration."""

    lang: str
    href: str

    def to_dict(self) -> Dict[str, Any]:
        return {"lang": self.lang, "href": self.href}


@dataclass
class TableData:
    """Represents a structured HTML table."""

    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"headers": self.headers, "rows": self.rows}


@dataclass
class Observation:
    """Epistemic technical or rendering observation with confidence rubric."""

    type: str  # e.g., "rendering_observation", "crawler_access", "schema_gap"
    value: str  # e.g., "server_html_appears_sparse", "nosnippet_detected"
    confidence: str  # "high", "medium", "low"
    evidence: str
    severity_hint: Optional[str] = None  # "critical", "high", "medium", "low"

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": self.type,
            "value": self.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }
        if self.severity_hint:
            data["severity_hint"] = self.severity_hint
        return data


@dataclass
class FactCandidate:
    """Atomic commercial or identity fact extracted with explicit provenance."""

    attribute: str  # "price", "currency", "phone", "email", "entity_name"
    value: Any
    currency: Optional[str] = None
    interval: Optional[str] = None  # "month", "year", "one_time"
    entity: Optional[str] = None
    source_url: str = ""
    locator: str = ""  # "Product.offers[0].price" or "xpath/selector"
    mechanism: str = "jsonld"  # "jsonld", "visible_text", "meta", "table"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "value": self.value,
            "currency": self.currency,
            "interval": self.interval,
            "entity": self.entity,
            "source_url": self.source_url,
            "locator": self.locator,
            "mechanism": self.mechanism,
        }


@dataclass
class ClaimCandidate:
    """Declarative claim with causal or statistical properties."""

    claim_text: str
    causal_type: Optional[str] = None  # "because", "due_to", "yields"
    statistical_proposition: bool = False
    source_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_text": self.claim_text,
            "causal_type": self.causal_type,
            "statistical_proposition": self.statistical_proposition,
            "source_url": self.source_url,
        }


@dataclass
class PageModel:
    """Enriched multi-signal representation of a crawled web page."""

    url: str
    final_url: str
    status: int
    content_type: str = "text/html"
    title: str = ""
    description: str = ""
    canonical: Optional[str] = None
    canonicals: List[str] = field(default_factory=list)
    robots_meta: List[str] = field(default_factory=list)
    language: Optional[str] = None
    headings: List[Heading] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    ctas: List[CTA] = field(default_factory=list)
    hreflangs: List[HreflangLink] = field(default_factory=list)
    social_links: List[str] = field(default_factory=list)
    contact_info: Dict[str, List[str]] = field(default_factory=dict)
    dates: Dict[str, Optional[str]] = field(default_factory=dict)
    x_robots_tag: List[str] = field(default_factory=list)
    redirect_chain: List[str] = field(default_factory=list)
    jsonld: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    clean_text: str = ""
    clean_markdown: str = ""
    word_count: int = 0
    snr: float = 0.0  # Signal-to-Noise Ratio: clean_text_bytes / raw_html_bytes
    page_type: Dict[str, Any] = field(default_factory=lambda: {"value": "unknown", "confidence": 0.5})
    semantic_landmarks: List[str] = field(default_factory=list)
    tables: List[TableData] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    facts: List[FactCandidate] = field(default_factory=list)
    claims: List[ClaimCandidate] = field(default_factory=list)
    fetch_telemetry: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    raw_html: str = ""
    truncated: bool = False

    def to_dict(self, include_raw_html: bool = False) -> Dict[str, Any]:
        """Convert page model to dictionary for JSON serialization."""
        data = {
            "url": self.url,
            "final_url": self.final_url,
            "redirect_chain": self.redirect_chain,
            "status": self.status,
            "truncated": self.truncated,
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "canonical": self.canonical,
            "canonicals": self.canonicals,
            "robots_meta": self.robots_meta,
            "x_robots_tag": self.x_robots_tag,
            "language": self.language,
            "hreflangs": [h.to_dict() for h in self.hreflangs],
            "headings": [h.to_dict() for h in self.headings],
            "links": [link.to_dict() for link in self.links],
            "ctas": [c.to_dict() for c in self.ctas],
            "social_links": self.social_links,
            "contact_info": self.contact_info,
            "dates": self.dates,
            "jsonld": self.jsonld,
            "metadata": self.metadata,
            "clean_text": self.clean_text,
            "clean_markdown": self.clean_markdown,
            "word_count": self.word_count,
            "snr": round(self.snr, 4),
            "text_density_ratio": round(self.snr, 4),
            "page_type": self.page_type,
            "semantic_landmarks": self.semantic_landmarks,
            "tables": [t.to_dict() for t in self.tables],
            "code_blocks": self.code_blocks,
            "images": self.images,
            "observations": [o.to_dict() for o in self.observations],
            "facts": [f.to_dict() for f in self.facts],
            "claims": [c.to_dict() for c in self.claims],
            "headers": self.headers,
            "fetch": self.fetch_telemetry,
        }
        if include_raw_html and self.raw_html:
            data["raw_html"] = self.raw_html
        return data


@dataclass
class EvidenceModel:
    """Master aggregate container linking pages, facts, claims, and observations."""

    site: str
    crawled_at: str
    pages: List[PageModel] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    facts: List[FactCandidate] = field(default_factory=list)
    claims: List[ClaimCandidate] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    scrapeability_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site": self.site,
            "crawled_at": self.crawled_at,
            "page_count": len(self.pages),
            "pages": [p.to_dict() for p in self.pages],
            "observations": [o.to_dict() for o in self.observations],
            "facts": [f.to_dict() for f in self.facts],
            "claims": [c.to_dict() for c in self.claims],
            "entities": self.entities,
            "scrapeability_summary": self.scrapeability_summary,
        }


# ==============================================================================
# SECTION 2: ZERO-TRUST SSRF SECURITY POLICY
# ==============================================================================

class SecurityValidationError(ValueError):
    """Raised when a URL or IP fails security validation."""


class SecurityPolicy:
    """Zero-trust SSRF validation policy for web requests and redirects."""

    ALLOWED_SCHEMES: Set[str] = {"http", "https"}

    # Cloud metadata and hazardous IP literals
    BLOCKED_IPS: Set[str] = {
        "169.254.169.254",  # AWS/GCP/Azure link-local metadata
        "169.254.170.2",    # AWS ECS task metadata
        "100.100.100.200",  # Alibaba Cloud metadata
        "0.0.0.0",
        "255.255.255.255",
    }

    # Hazardous hostnames
    BLOCKED_HOSTNAMES: Set[str] = {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "instance-data",
    }

    def __init__(
        self,
        allow_private_ips: bool = False,
        require_https: bool = False,
        allow_downgrade_redirects: bool = False,
    ) -> None:
        self.allow_private_ips = allow_private_ips
        self.require_https = require_https
        self.allow_downgrade_redirects = allow_downgrade_redirects

    def is_ip_safe(self, ip_str: str) -> Tuple[bool, str]:
        """Classify an IP string against SSRF blacklists."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Malformed IP address literal: {ip_str}"

        # Check explicit blacklisted IPs
        if ip_str in self.BLOCKED_IPS:
            return False, f"Blocked metadata or reserved IP address: {ip_str}"

        # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
            mapped_ipv4 = ip_obj.ipv4_mapped
            return self.is_ip_safe(str(mapped_ipv4))

        if not self.allow_private_ips:
            if ip_obj.is_loopback:
                return False, f"Loopback address rejected: {ip_str}"
            if ip_obj.is_private:
                return False, f"Private address (RFC 1918 / RFC 4193) rejected: {ip_str}"
            if ip_obj.is_link_local:
                return False, f"Link-local address rejected: {ip_str}"
            if ip_obj.is_reserved:
                return False, f"Reserved address rejected: {ip_str}"
            if ip_obj.is_multicast:
                return False, f"Multicast address rejected: {ip_str}"
            if ip_obj.is_unspecified:
                return False, f"Unspecified address rejected: {ip_str}"

            # Check Carrier-Grade NAT (RFC 6598: 100.64.0.0/10)
            if isinstance(ip_obj, ipaddress.IPv4Address):
                cgnat = ipaddress.IPv4Network("100.64.0.0/10")
                if ip_obj in cgnat:
                    return False, f"Carrier-grade NAT address (RFC 6598) rejected: {ip_str}"

        return True, "Public IP verified / permissible"

    def resolve_and_verify_host(self, host: str, port: int = 443) -> Tuple[bool, str, Optional[str]]:
        """Pre-resolve hostname via DNS and check all returned IPs for safety."""
        clean_host = host.strip().lower().strip("[]")
        if not clean_host:
            return False, "Empty hostname", None

        if clean_host in self.BLOCKED_HOSTNAMES or clean_host.endswith(".internal") or clean_host.endswith(".local"):
            return False, f"Blocked internal hostname: {clean_host}", None

        # If host is already an IP address
        try:
            ip_obj = ipaddress.ip_address(clean_host)
            safe, reason = self.is_ip_safe(str(ip_obj))
            return safe, reason, str(ip_obj)
        except ValueError:
            pass  # It's a hostname, proceed to DNS resolution

        # Resolve via DNS
        try:
            addr_info = socket.getaddrinfo(
                clean_host,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        except (socket.gaierror, socket.herror, OSError) as e:
            return False, f"DNS resolution failed for {clean_host}: {e}", None

        if not addr_info:
            return False, f"No DNS records found for {clean_host}", None

        resolved_ip: Optional[str] = None
        for _, _, _, _, sockaddr in addr_info:
            ip_str = str(sockaddr[0])
            safe, reason = self.is_ip_safe(ip_str)
            if not safe:
                return False, f"Host {clean_host} resolved to disallowed IP ({ip_str}): {reason}", None
            if resolved_ip is None:
                resolved_ip = ip_str

        return True, "Host resolution verified safe", resolved_ip

    def validate_url(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """Validate target URL for scheme, hostname, and IP safety."""
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Failed to parse URL: {e}", None

        scheme = parsed.scheme.lower()
        if scheme not in self.ALLOWED_SCHEMES:
            return False, f"Disallowed URL scheme: {scheme} (only HTTP/HTTPS permitted)", None

        if self.require_https and scheme != "https":
            return False, "HTTPS is strictly required by policy", None

        host = parsed.hostname
        if not host:
            return False, "Missing hostname in URL", None

        port = parsed.port
        if port is not None and port not in (80, 443):
            return False, f"Disallowed port: {port}. Only standard web ports (80, 443) are permitted", None
        port = port or (443 if scheme == "https" else 80)
        return self.resolve_and_verify_host(host, port)

    def validate_redirect(
        self, original_url: str, new_location: str
    ) -> Tuple[bool, str, str, Optional[str]]:
        """Validate a redirect target URL and prevent scheme downgrade or SSRF evasion."""
        resolved_new_url = urljoin(original_url, new_location)
        orig_parsed = urlparse(original_url)
        new_parsed = urlparse(resolved_new_url)

        # Prevent HTTPS to HTTP downgrade if policy prohibits
        if not self.allow_downgrade_redirects and orig_parsed.scheme == "https" and new_parsed.scheme == "http":
            return False, "Insecure scheme downgrade from HTTPS to HTTP blocked", resolved_new_url, None

        safe, reason, ip = self.validate_url(resolved_new_url)
        if not safe:
            return False, f"Redirect target rejected: {reason}", resolved_new_url, None

        return True, "Redirect target is safe", resolved_new_url, ip

    def validate_url_and_resolve(self, url: str) -> Tuple[str, str, int]:
        """Validate target URL and resolve IP address, raising SecurityValidationError on failure."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        port = parsed.port or (443 if scheme == "https" else 80)
        safe, reason, ip = self.validate_url(url)
        if not safe or not ip:
            raise SecurityValidationError(reason)
        return scheme, ip, port


# ==============================================================================
# SECTION 3: RESOURCE BUDGET & CONCURRENCY
# ==============================================================================

class BudgetExhaustedError(RuntimeError):
    """Raised when an operation would exceed the allocated audit budget."""


class Budget:
    """Enforces resource limits and monotonic deadlines across crawler components."""

    def __init__(
        self,
        time_limit_sec: float = 180.0,
        max_pages: int = 28,
        max_total_bytes: int = 50 * 1024 * 1024,
        max_page_bytes: int = 2500000,
        max_depth: int = 3,
        max_redirects: int = 5,
        max_concurrency: int = 8,
    ) -> None:
        self.time_limit_sec = float(time_limit_sec)
        self.max_pages = int(max_pages)
        self.max_total_bytes = int(max_total_bytes)
        self.max_page_bytes = int(max_page_bytes)
        self.max_depth = int(max_depth)
        self.max_redirects = int(max_redirects)
        self.max_concurrency = int(max_concurrency)

        self._start_time = time.monotonic()
        self._deadline = self._start_time + self.time_limit_sec
        self._requests_made = 0
        self._pages_fetched = 0
        self._pages_reserved = 0
        self._bytes_downloaded = 0
        self._lock = threading.RLock()

    def remaining_time(self) -> float:
        """Returns the number of seconds remaining before the deadline (minimum 0.0)."""
        rem = self._deadline - time.monotonic()
        return max(0.0, rem)

    def elapsed_time(self) -> float:
        """Returns the total elapsed seconds since budget inception."""
        return time.monotonic() - self._start_time

    def is_exhausted(self) -> bool:
        """Checks whether time, page count, or byte budget has been exhausted."""
        with self._lock:
            return (
                time.monotonic() >= self._deadline
                or self._pages_fetched >= self.max_pages
                or self._bytes_downloaded >= self.max_total_bytes
            )

    def can_fetch_page(self, depth: int = 0) -> bool:
        """Determines if another page can be fetched within depth and resource constraints."""
        if depth > self.max_depth:
            return False
        with self._lock:
            return (
                time.monotonic() < self._deadline
                and (self._pages_fetched + self._pages_reserved) < self.max_pages
                and self._bytes_downloaded < self.max_total_bytes
            )

    def reserve_page_slot(self, depth: int = 0) -> bool:
        """Atomically reserves a page slot for an in-flight worker task."""
        if depth > self.max_depth:
            return False
        with self._lock:
            if (
                time.monotonic() < self._deadline
                and (self._pages_fetched + self._pages_reserved) < self.max_pages
                and self._bytes_downloaded < self.max_total_bytes
            ):
                self._pages_reserved += 1
                return True
            return False

    def commit_page_slot(self) -> None:
        """Atomically commits a successfully fetched HTML page, decrementing reservation."""
        with self._lock:
            if self._pages_reserved > 0:
                self._pages_reserved -= 1
            self._pages_fetched += 1

    def release_page_slot(self) -> None:
        """Atomically releases a reserved page slot on fetch failure or non-HTML resource."""
        with self._lock:
            if self._pages_reserved > 0:
                self._pages_reserved -= 1

    def record_request(self) -> None:
        """Thread-safely records an HTTP request attempt (infrastructure or page)."""
        with self._lock:
            self._requests_made += 1

    def record_page(self) -> None:
        """Thread-safely records a completed HTML content page fetch."""
        with self._lock:
            self._pages_fetched += 1

    def record_bytes(self, count: int) -> None:
        """Thread-safely records bytes received."""
        with self._lock:
            self._bytes_downloaded += max(0, count)

    def check_or_raise(self) -> None:
        """Raises BudgetExhaustedError if the budget is exhausted."""
        if self.is_exhausted():
            raise BudgetExhaustedError(
                f"Audit budget exhausted: elapsed={self.elapsed_time():.1f}s, "
                f"pages={self._pages_fetched}/{self.max_pages}, "
                f"bytes={self._bytes_downloaded}/{self.max_total_bytes}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Returns current resource utilization metrics."""
        with self._lock:
            return {
                "elapsed_sec": round(self.elapsed_time(), 2),
                "remaining_sec": round(self.remaining_time(), 2),
                "requests_made": self._requests_made,
                "pages_fetched": self._pages_fetched,
                "max_pages": self.max_pages,
                "bytes_downloaded": self._bytes_downloaded,
                "max_total_bytes": self.max_total_bytes,
                "is_exhausted": self.is_exhausted(),
            }


# ==============================================================================
# SECTION 4: PRIORITY URL FRONTIER & ROUTE WEIGHT SCORING
# ==============================================================================

@dataclass(order=True)
class FrontierItem:
    """Prioritized queue item for the crawler frontier."""

    neg_priority: float
    depth: int
    url: str = field(compare=False)
    source_url: Optional[str] = field(default=None, compare=False)
    is_sitemap_declared: bool = field(default=False, compare=False)

    @property
    def priority(self) -> float:
        return -self.neg_priority


class Frontier:
    """Thread-safe prioritized URL queue with intelligent route scoring and deduplication."""

    ROUTE_WEIGHTS: Dict[str, float] = {
        "/": 100.0,
        "pricing": 95.0,
        "prices": 95.0,
        "plans": 95.0,
        "billing": 95.0,
        "product": 90.0,
        "products": 90.0,
        "shop": 90.0,
        "store": 90.0,
        "catalog": 90.0,
        "collection": 88.0,
        "collections": 88.0,
        "solutions": 90.0,
        "features": 88.0,
        "platform": 88.0,
        "capabilities": 88.0,
        "about": 85.0,
        "about-us": 85.0,
        "company": 85.0,
        "services": 85.0,
        "service": 85.0,
        "contact": 80.0,
        "contact-us": 80.0,
        "support": 75.0,
        "help": 75.0,
        "docs": 75.0,
        "documentation": 75.0,
        "api": 70.0,
        "developers": 70.0,
        "faq": 70.0,
        "faqs": 70.0,
        "customers": 60.0,
        "case-studies": 60.0,
        "blog": 45.0,
        "news": 45.0,
        "press": 40.0,
        "terms": 30.0,
        "privacy": 30.0,
        "legal": 30.0,
        "cookie": 25.0,
        "cookies": 25.0,
        "cart": 55.0,
        "checkout": 55.0,
        "subscription": 92.0,
        "subscribe": 92.0,
        "coffee": 88.0,
        "login": 50.0,
        "signin": 50.0,
        "signup": 50.0,
        "register": 50.0,
        "auth": 45.0,
        "quiz": 70.0,
        "admin": 5.0,
    }

    def __init__(self, max_capacity: int = 2000) -> None:
        self.max_capacity = max_capacity
        self._heap: list[FrontierItem] = []
        self._enqueued: Set[str] = set()
        self._visited: Set[str] = set()
        self._lock = threading.Lock()

    def compute_priority(
        self,
        url: str,
        depth: int,
        is_sitemap_declared: bool = False,
        source_url: Optional[str] = None,
    ) -> float:
        """Computes a numeric priority score for a given URL."""
        parsed = urlparse(url)
        path = (parsed.path or "/").lower().strip("/")

        base_score = 40.0
        if not path:
            base_score = self.ROUTE_WEIGHTS["/"]
        else:
            segments = path.split("/")
            first_seg = segments[0]
            if first_seg in self.ROUTE_WEIGHTS:
                base_score = self.ROUTE_WEIGHTS[first_seg]
            else:
                for route_key, weight in self.ROUTE_WEIGHTS.items():
                    if route_key in path:
                        base_score = max(base_score, weight * 0.9)

        # Asset / DAM / media paths are low-priority for content audit
        asset_penalty = 0.0
        if any(seg in path for seg in ("content/dam", "/dam/", "dam/", "/assets/", "/media/", "/static/", "/uploads/", "/images/")):
            asset_penalty = 60.0

        # Direct homepage/seed links receive higher priority than arbitrary sitemap URLs
        seed_link_bonus = 30.0 if (depth <= 1 and not is_sitemap_declared) else 0.0
        sitemap_bonus = 15.0 if is_sitemap_declared else 0.0
        depth_penalty = depth * 12.0
        query_penalty = 10.0 if parsed.query else 0.0
        return base_score + seed_link_bonus + sitemap_bonus - depth_penalty - query_penalty - asset_penalty

    def push(
        self,
        url: str,
        depth: int = 0,
        is_sitemap_declared: bool = False,
        source_url: Optional[str] = None,
    ) -> bool:
        """Pushes a URL to the frontier if not already seen or enqueued. Returns True if accepted."""
        with self._lock:
            if url in self._enqueued or url in self._visited:
                return False
            if len(self._enqueued) >= self.max_capacity:
                return False

            priority = self.compute_priority(url, depth, is_sitemap_declared, source_url=source_url)
            item = FrontierItem(
                neg_priority=-priority,
                depth=depth,
                url=url,
                source_url=source_url,
                is_sitemap_declared=is_sitemap_declared,
            )
            heapq.heappush(self._heap, item)
            self._enqueued.add(url)
            return True

    def pop(self) -> Optional[FrontierItem]:
        """Pops the highest priority URL from the queue."""
        with self._lock:
            while self._heap:
                item = heapq.heappop(self._heap)
                if item.url not in self._visited:
                    self._visited.add(item.url)
                    return item
            return None

    def mark_visited(self, url: str) -> None:
        with self._lock:
            self._visited.add(url)

    def has_visited(self, url: str) -> bool:
        with self._lock:
            return url in self._visited

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._heap) == 0

    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def total_seen(self) -> int:
        with self._lock:
            return len(self._enqueued)


# ==============================================================================
# SECTION 5: CANONICAL VALIDATOR & PAGE CLASSIFIER
# ==============================================================================

class CanonicalValidator:
    """Evaluates canonical URL declarations for SEO and machine discoverability defects."""

    @classmethod
    def evaluate(
        cls, current_url: str, canonical_url: Optional[str]
    ) -> Tuple[bool, List[Observation]]:
        observations: List[Observation] = []

        if not canonical_url or not canonical_url.strip():
            observations.append(
                Observation(
                    type="canonical_gap",
                    value="missing_canonical_tag",
                    confidence="high",
                    evidence=f"No <link rel='canonical'> specified on {current_url}",
                    severity_hint="medium",
                )
            )
            return False, observations

        clean_canonical = canonical_url.strip()
        try:
            curr_parsed = urlparse(current_url)
            canon_parsed = urlparse(clean_canonical)
        except Exception:
            observations.append(
                Observation(
                    type="canonical_defect",
                    value="malformed_canonical_url",
                    confidence="high",
                    evidence=f"Malformed canonical tag '{clean_canonical}' on {current_url}",
                    severity_hint="high",
                )
            )
            return False, observations

        # Protocol mismatch check
        if curr_parsed.scheme == "https" and canon_parsed.scheme == "http":
            observations.append(
                Observation(
                    type="canonical_defect",
                    value="protocol_downgrade",
                    confidence="high",
                    evidence=f"Secure HTTPS page canonicalizes to insecure HTTP target: {clean_canonical}",
                    severity_hint="high",
                )
            )

        # Cross-domain canonical check
        curr_host = (curr_parsed.hostname or "").lower()
        canon_host = (canon_parsed.hostname or "").lower()
        if canon_host and curr_host != canon_host:
            observations.append(
                Observation(
                    type="canonical_cross_domain",
                    value="cross_domain_canonical_detected",
                    confidence="medium",
                    evidence=f"Page on host '{curr_host}' points to canonical target on '{canon_host}'",
                    severity_hint="medium",
                )
            )

        has_defect = any(
            obs.type in ("canonical_gap", "canonical_defect", "canonical_cross_domain")
            for obs in observations
        )
        return not has_defect, observations


class PageClassifier:
    """Classifies web pages using URL path tokens, title, headings, and schema types."""

    PATTERNS = {
        "homepage": [r"^/?$", r"^/index\.(html?|php)$"],
        "pricing": [r"/pricing/?", r"/plans/?", r"/pricing-plans/?", r"/cost/?"],
        "product_detail": [
            r"/products?/[^/]+",
            r"/items?/[^/]+",
            r"/p/[^/]+",
            r"/goods/[^/]+",
            r"/dp/[^/]+",
        ],
        "about": [r"/about(-us)?/?", r"/company/?", r"/team/?", r"/our-story/?"],
        "contact": [r"/contact(-us)?/?", r"/support/?", r"/help(desk)?/?"],
        "documentation": [r"/docs?(/.*)?", r"/documentation(/.*)?", r"/api(/.*)?", r"/developers(/.*)?"],
        "faq": [r"/faqs?/?", r"/frequently-asked-questions/?"],
        "article": [r"/blog/[^/]+", r"/news/[^/]+", r"/articles?/[^/]+", r"/posts?/[^/]+"],
        "category": [r"/categories?/?.*", r"/collections?/?.*", r"/catalog/?.*"],
    }

    @classmethod
    def classify(
        cls,
        url: str,
        title: str = "",
        schemas: Optional[List[Dict[str, Any]]] = None,
        headings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        parsed = urlparse(url)
        path = (parsed.path or "/").lower()

        # Step 1: Check schema hints first (highest semantic ground truth)
        if schemas:
            schema_types = []
            for s in schemas:
                st = s.get("@type")
                if isinstance(st, str):
                    schema_types.append(st)
                elif isinstance(st, list):
                    schema_types.extend(st)

            if any("FAQPage" in st for st in schema_types):
                return {"value": "faq", "confidence": 0.95}
            if any("Product" in st for st in schema_types):
                return {"value": "product_detail", "confidence": 0.92}
            if any(t in schema_types for t in ["Article", "NewsArticle", "BlogPosting"]):
                return {"value": "article", "confidence": 0.90}

        # Step 2: Check URL path patterns
        for ptype, regex_list in cls.PATTERNS.items():
            for regex in regex_list:
                if re.search(regex, path):
                    return {"value": ptype, "confidence": 0.85}

        # Step 3: Heuristic check based on title and headings
        title_lower = title.lower()
        if any(cp in title_lower for cp in ("just a moment", "attention required", "security challenge", "security check", "cloudflare", "403 forbidden", "robot or human", "bot challenge")):
            return {"value": "bot_challenge", "confidence": 0.99}
        if "pricing" in title_lower or "plans" in title_lower:
            return {"value": "pricing", "confidence": 0.75}
        if "frequently asked questions" in title_lower or "faq" in title_lower:
            return {"value": "faq", "confidence": 0.80}
        if "about us" in title_lower or "our mission" in title_lower:
            return {"value": "about", "confidence": 0.75}
        if "contact us" in title_lower or "get in touch" in title_lower:
            return {"value": "contact", "confidence": 0.75}

        if path in {"", "/"}:
            return {"value": "homepage", "confidence": 0.99}

        return {"value": "general", "confidence": 0.50}

    @classmethod
    def classify_route(cls, url: str) -> str:
        res = cls.classify(url)
        val = res.get("value", "general")
        if val == "product_detail":
            return "product"
        return val


# ==============================================================================
# SECTION 6: STREAMING HTTP FETCHER & PINNED CONNECTIONS
# ==============================================================================

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


class PinnedConnectionPool:
    """Tracks pinned IPs per hostname to ensure DNS TOCTOU protection across redirects."""

    def __init__(self, policy: SecurityPolicy, initial_host: str, initial_ip: Optional[str] = None) -> None:
        self.policy = policy
        clean_init = initial_host.lower().strip("[]")
        self.host_to_ip: Dict[str, str] = {}
        if initial_ip:
            self.host_to_ip[clean_init] = initial_ip
        self.last_connected_ip: Optional[str] = initial_ip

    def get_or_resolve_ip(self, host: str, port: int) -> str:
        clean_host = host.lower().strip("[]")
        if clean_host in self.host_to_ip:
            ip = self.host_to_ip[clean_host]
            self.last_connected_ip = ip
            return ip
        safe, reason, resolved_ip = self.policy.resolve_and_verify_host(clean_host, port)
        if not safe or not resolved_ip:
            raise SecurityValidationError(f"SSRF rejection during connection to {clean_host}: {reason}")
        self.host_to_ip[clean_host] = resolved_ip
        self.last_connected_ip = resolved_ip
        return resolved_ip


class PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection that connects directly to a pre-validated IP address."""

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        timeout: float = 15.0,
        pool: Optional[PinnedConnectionPool] = None,
        pinned_ip: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(host, port, timeout=timeout, **kwargs)
        self.pool = pool
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        clean_host = self.host.strip("[]")
        if self.pool:
            target_ip = self.pool.get_or_resolve_ip(clean_host, self.port or 80)
        else:
            target_ip = self.pinned_ip or clean_host
        source_addr = getattr(self, "source_address", None)
        self.sock = socket.create_connection((target_ip, self.port), self.timeout, source_addr)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection that connects directly to a pre-validated IP address with TLS SNI verification."""

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        timeout: float = 15.0,
        pool: Optional[PinnedConnectionPool] = None,
        pinned_ip: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(host, port, timeout=timeout, **kwargs)
        self.pool = pool
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        clean_host = self.host.strip("[]")
        if self.pool:
            target_ip = self.pool.get_or_resolve_ip(clean_host, self.port or 443)
        else:
            target_ip = self.pinned_ip or clean_host
        source_addr = getattr(self, "source_address", None)
        self.sock = socket.create_connection((target_ip, self.port), self.timeout, source_addr)
        if getattr(self, "_tunnel_host", None):
            tunnel_fn = getattr(self, "_tunnel", None)
            if callable(tunnel_fn):
                tunnel_fn()
        server_hostname = clean_host
        ctx = getattr(self, "_context", None) or ssl.create_default_context()
        self.sock = ctx.wrap_socket(self.sock, server_hostname=server_hostname)


class PinnedHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, pool: Optional[PinnedConnectionPool] = None, pinned_ip: Optional[str] = None) -> None:
        super().__init__()
        self.pool = pool
        self.pinned_ip = pinned_ip

    def http_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(
            lambda host, port=None, timeout=15.0, **kwargs: PinnedHTTPConnection(
                host, port, timeout=timeout, pool=self.pool, pinned_ip=self.pinned_ip, **kwargs
            ),
            req,
        )


class PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(
        self, context: ssl.SSLContext, pool: Optional[PinnedConnectionPool] = None, pinned_ip: Optional[str] = None
    ) -> None:
        super().__init__(context=context)
        self.pool = pool
        self.pinned_ip = pinned_ip
        self.ssl_context = context

    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(
            lambda host, port=None, timeout=15.0, **kwargs: PinnedHTTPSConnection(
                host, port, timeout=timeout, pool=self.pool, pinned_ip=self.pinned_ip, **{**kwargs, "context": self.ssl_context}
            ),
            req,
            context=self.ssl_context,
        )


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Intercepts HTTP redirects to enforce SSRF validation and redirect ceilings."""

    def __init__(
        self, policy: SecurityPolicy, pool: Optional[PinnedConnectionPool] = None, max_redirects: int = 5
    ) -> None:
        super().__init__()
        self.policy = policy
        self.pool = pool
        self.max_redirects = max_redirects
        self.redirect_chain: List[str] = []

    def redirect_request(
        self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Optional[urllib.request.Request]:
        if len(self.redirect_chain) >= self.max_redirects:
            raise SecurityValidationError(f"Exceeded maximum redirects ceiling ({self.max_redirects})")

        original_url = req.full_url
        safe, reason, resolved_url, target_ip = self.policy.validate_redirect(original_url, newurl)
        if not safe:
            raise SecurityValidationError(f"Redirect security rejection: {reason}")

        if self.pool and target_ip:
            new_parsed = urllib.parse.urlparse(resolved_url)
            if new_parsed.hostname:
                self.pool.host_to_ip[new_parsed.hostname.lower().strip("[]")] = target_ip

        self.redirect_chain.append(resolved_url)
        return super().redirect_request(req, fp, code, msg, headers, resolved_url)


class SafeFetcher:
    """Zero-dependency HTTP client configured with security guardrails and budget limits."""

    CHUNK_SIZE = 8192
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandAuditBot; +https://agentskills.io/bot)"

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
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            self.budget.check_or_raise()

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

            parsed_initial = urllib.parse.urlparse(url)
            initial_host = parsed_initial.hostname or ""
            pool = PinnedConnectionPool(policy=self.policy, initial_host=initial_host, initial_ip=resolved_ip)

            redirect_handler = SafeRedirectHandler(
                policy=self.policy, pool=pool, max_redirects=self.budget.max_redirects
            )
            http_handler = PinnedHTTPHandler(pool=pool, pinned_ip=resolved_ip)
            https_handler = PinnedHTTPSHandler(context=self.ssl_context, pool=pool, pinned_ip=resolved_ip)
            proxy_handler = urllib.request.ProxyHandler({})  # Explicitly disable ambient environment proxies
            opener = urllib.request.build_opener(proxy_handler, redirect_handler, http_handler, https_handler)

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
                    is_truncated = False

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
                            is_truncated = True
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
                        ip_address=pool.last_connected_ip or resolved_ip,
                        truncated=is_truncated,
                    )

            except urllib.error.HTTPError as e:
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
                decompressed_error = self._decompress_body(error_body, resp_headers.get("content-encoding"))
                return Resource(
                    url=url,
                    final_url=getattr(e, "url", getattr(e, "geturl", lambda: url)()),
                    status=e.code,
                    headers=resp_headers,
                    body_bytes=decompressed_error,
                    content_type=resp_headers.get("content-type", "text/html"),
                    latency_ms=latency_ms,
                    redirects=redirect_handler.redirect_chain,
                    ip_address=pool.last_connected_ip or resolved_ip,
                )

            except urllib.error.URLError as e:
                latency_ms = (time.monotonic() - start_time) * 1000.0
                raise ConnectionError(f"Network transport error for {url}: {e.reason}") from e

        raise ConnectionError(f"Fetch failed for {url} after {max_attempts} attempts.")

    def _decompress_body(self, raw_data: bytes, encoding: Optional[str], max_decoded_bytes: Optional[int] = None) -> bytes:
        if not raw_data or not encoding:
            return raw_data

        limit = max_decoded_bytes or self.budget.max_page_bytes
        enc = encoding.strip().lower()

        if enc in ("gzip", "deflate"):
            wbits = (16 + zlib.MAX_WBITS) if enc == "gzip" else zlib.MAX_WBITS
            try:
                dobj = zlib.decompressobj(wbits)
                decompressed_chunks: List[bytes] = []
                total_len = 0
                chunk_len = 16384
                for i in range(0, len(raw_data), chunk_len):
                    remaining_bound = max(0, limit - total_len)
                    chunk = dobj.decompress(raw_data[i:i + chunk_len], remaining_bound)
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
                        dobj = zlib.decompressobj(-zlib.MAX_WBITS)
                        return dobj.decompress(raw_data)[:limit]
                    except zlib.error:
                        return raw_data
                return raw_data
        return raw_data


# ==============================================================================
# SECTION 7: RFC 9309 ROBOTS.TXT AUDITOR
# ==============================================================================

AI_CRAWLER_BOTS: List[str] = [
    "OAI-SearchBot",
    "Claude-SearchBot",
    "PerplexityBot",
    "Amazonbot",
    "cohere-ai",
    "Meta-ExternalAgent",
    "Claude-User",
    "Perplexity-User",
    "ChatGPT-User",
    "GPTBot",
    "ClaudeBot",
    "Bytespider",
    "Applebot-Extended",
    "Google-Extended",
    "CCBot",
    "*",
]

MAX_ROBOTS_BYTES = 500 * 1024


class RobotsOutcome:
    OK = "robots_ok"
    NOT_FOUND = "robots_not_found"
    BLOCKED = "robots_blocked"
    SERVER_ERROR = "robots_server_error"
    TIMEOUT = "robots_timeout"
    PARSE_ERROR = "robots_parse_error"


BOT_TAXONOMY: Dict[str, Dict[str, str]] = {
    "OAI-SearchBot": {"role": "search_crawler", "provider": "OpenAI", "description": "Search indexation crawler for ChatGPT Search"},
    "Claude-SearchBot": {"role": "search_crawler", "provider": "Anthropic", "description": "Search indexation crawler for Claude"},
    "PerplexityBot": {"role": "search_crawler", "provider": "Perplexity", "description": "Search retrieval crawler for Perplexity AI"},
    "Amazonbot": {"role": "search_crawler", "provider": "Amazon", "description": "Web crawler for Alexa and Amazon AI"},
    "cohere-ai": {"role": "training_bot", "provider": "Cohere", "description": "Model pretraining web crawler"},
    "Meta-ExternalAgent": {"role": "search_crawler", "provider": "Meta", "description": "Search crawler for Meta AI"},
    "Claude-User": {"role": "user_directed_fetch", "provider": "Anthropic", "description": "On-demand user request fetcher for Claude"},
    "Perplexity-User": {"role": "user_directed_fetch", "provider": "Perplexity", "description": "On-demand user query fetcher for Perplexity"},
    "ChatGPT-User": {"role": "user_directed_fetch", "provider": "OpenAI", "description": "On-demand browsing fetcher for ChatGPT"},
    "GPTBot": {"role": "training_bot", "provider": "OpenAI", "description": "AI model training and fine-tuning crawler"},
    "ClaudeBot": {"role": "training_bot", "provider": "Anthropic", "description": "AI model training crawler"},
    "Bytespider": {"role": "training_bot", "provider": "ByteDance", "description": "AI model training crawler"},
    "Applebot-Extended": {"role": "training_bot", "provider": "Apple", "description": "Control token for Apple Intelligence model training"},
    "Google-Extended": {"role": "control_token", "provider": "Google", "description": "Control token for Gemini and Vertex AI training"},
    "CCBot": {"role": "training_bot", "provider": "Common Crawl", "description": "Open web crawl repository for pretraining"},
    "*": {"role": "wildcard", "provider": "Universal", "description": "Default crawler fallback directive"},
}


def robot_octets(value: str) -> str:
    value = quote(value, safe="/%*?$&=:@!+,'();~-._")

    def replace(match: Any) -> str:
        c = chr(int(match.group(1), 16))
        return c if c.isascii() and (c.isalnum() or c in "-._~") else "%" + match.group(1).upper()

    return re.sub(r"%([0-9a-fA-F]{2})", replace, value)


class RobotsRule:
    """Represents an Allow or Disallow rule with longest-match pattern matching."""

    def __init__(self, is_allow: bool, pattern: str) -> None:
        self.is_allow = is_allow
        self.raw_pattern = pattern
        self.pattern = robot_octets(pattern)
        self.terminal = self.pattern.endswith("$")
        pat_clean = self.pattern[:-1] if self.terminal else self.pattern
        regex = "^" + ".*".join(re.escape(x) for x in pat_clean.split("*")) + ("$" if self.terminal else "")
        self._compiled_regex = re.compile(regex)

    def matches(self, path: str) -> bool:
        norm_path = robot_octets(path)
        return bool(self._compiled_regex.search(norm_path))

    @property
    def length(self) -> int:
        pat = self.pattern[:-1] if self.terminal else self.pattern
        return len(re.sub(r"%[A-F0-9]{2}", "x", pat.replace("*", "")))


class RobotsGroup:
    """A collection of rules belonging to one or more user-agent identifiers."""

    def __init__(self) -> None:
        self.user_agents: Set[str] = set()
        self.rules: List[RobotsRule] = []
        self.crawl_delay: Optional[float] = None

    def applies_to(self, target_agent: str) -> bool:
        target_lower = target_agent.lower()
        return any(ua.lower() == target_lower or ua == "*" for ua in self.user_agents)


class RobotsAuditor:
    """Parser and evaluator for robots.txt files conforming to RFC 9309."""

    def __init__(self, content: str = "", status_code: int = 200, outcome: str = RobotsOutcome.OK) -> None:
        self.raw_content = content[:MAX_ROBOTS_BYTES]
        self.status_code = status_code
        self.outcome = outcome
        self.groups: List[RobotsGroup] = []
        self.sitemaps: List[str] = []
        self._parse()

    def _parse(self) -> None:
        if not self.raw_content or self.status_code == 404:
            return

        current_group: Optional[RobotsGroup] = None
        lines = self.raw_content.splitlines()

        for line in lines:
            line = line.strip()
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue

            field_name, value = [p.strip() for p in line.split(":", 1)]
            field_lower = field_name.lower()

            if field_lower == "user-agent":
                if current_group is None or current_group.rules:
                    current_group = RobotsGroup()
                    self.groups.append(current_group)
                current_group.user_agents.add(value)

            elif field_lower == "disallow":
                if current_group is not None and value:
                    current_group.rules.append(RobotsRule(is_allow=False, pattern=value))

            elif field_lower == "allow":
                if current_group is not None and value:
                    current_group.rules.append(RobotsRule(is_allow=True, pattern=value))

            elif field_lower == "crawl-delay":
                if current_group is not None:
                    try:
                        current_group.crawl_delay = float(value)
                    except ValueError:
                        pass

            elif field_lower == "sitemap":
                if value and value not in self.sitemaps:
                    self.sitemaps.append(value)

    def is_allowed(self, user_agent: str, url_or_path: str = "") -> bool:
        if user_agent.startswith(("http://", "https://", "/")) and not url_or_path.startswith(("http://", "https://", "/")):
            user_agent, url_or_path = url_or_path, user_agent

        if self.outcome == RobotsOutcome.BLOCKED or self.status_code in (401, 403):
            return False

        if self.outcome == RobotsOutcome.SERVER_ERROR or self.status_code >= 500 or self.status_code == 429:
            return False

        if self.outcome == RobotsOutcome.NOT_FOUND or self.status_code == 404:
            return True

        parsed = urlparse(url_or_path)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        matching_rules: List[RobotsRule] = []
        agent_lower = user_agent.lower()
        agent_product = re.split(r"[/;\s]", agent_lower)[0].strip()

        matched_specific = False
        for group in self.groups:
            for ua in group.user_agents:
                ua_clean = ua.strip().lower()
                if ua_clean == "*":
                    continue
                rule_product = re.split(r"[/;\s]", ua_clean)[0].strip()
                is_match = (
                    ua_clean == agent_lower
                    or rule_product == agent_product
                    or (agent_lower.startswith(ua_clean) and (len(agent_lower) == len(ua_clean) or agent_lower[len(ua_clean)] in ("/", "-", " ")))
                    or (ua_clean.startswith(agent_product) and (len(ua_clean) == len(agent_product) or ua_clean[len(agent_product)] in ("/", "-", " ")))
                )
                if is_match:
                    matching_rules.extend(group.rules)
                    matched_specific = True
                    break

        if not matched_specific:
            for group in self.groups:
                for ua in group.user_agents:
                    if ua.strip() == "*":
                        matching_rules.extend(group.rules)
                        break

        if not matching_rules:
            return True

        best_match: Optional[RobotsRule] = None
        for rule in matching_rules:
            if rule.matches(path) and (
                best_match is None
                or rule.length > best_match.length
                or (rule.length == best_match.length and rule.is_allow and not best_match.is_allow)
            ):
                best_match = rule

        if best_match is None:
            return True
        return best_match.is_allow

    def evaluate_ai_bots_matrix(self, path: str = "/") -> Dict[str, Dict[str, Any]]:
        matrix: Dict[str, Dict[str, Any]] = {}
        for bot in AI_CRAWLER_BOTS:
            allowed = self.is_allowed(bot, path)
            tax = BOT_TAXONOMY.get(bot, {"role": "unknown", "provider": "Unknown", "description": "AI bot"})
            matrix[bot] = {
                "allowed": allowed,
                "status": "allowed" if allowed else "blocked",
                "role": tax.get("role", "unknown"),
                "provider": tax.get("provider", "Unknown"),
                "description": tax.get("description", ""),
            }
        return matrix

    @property
    def delay(self) -> float:
        delays = [g.crawl_delay for g in self.groups if g.crawl_delay is not None]
        return max(delays) if delays else 1.0

    def allowed(self, url_or_path: str, user_agent: str = "ReadinessAudit") -> bool:
        return self.is_allowed(user_agent, url_or_path)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "outcome": self.outcome,
            "sitemaps": self.sitemaps,
            "groups_count": len(self.groups),
            "ai_bots_matrix": self.evaluate_ai_bots_matrix("/"),
        }


# Standard alias for compatibility with test harnesses and single-pass collectors
Robots = RobotsAuditor


def load_bot_registry() -> Dict[str, Any]:
    """Load authoritative bot registry from references/bot-registry.json if available."""
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "references",
        "bot-registry.json",
    )
    if os.path.exists(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"version": "2026-09-01", "bots": []}


# ==============================================================================
# SECTION 8: XML SITEMAP DISCOVERER & PARSER
# ==============================================================================

@dataclass
class SitemapUrl:
    """Represents a URL entry in an XML sitemap."""

    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "loc": self.loc,
            "lastmod": self.lastmod,
            "changefreq": self.changefreq,
            "priority": self.priority,
        }


class SitemapParser:
    """Parses XML sitemap payloads with XML-safe namespace stripping and regex fallback."""

    _NS_REGEX = re.compile(r"\{[^\}]+\}")
    _URL_LOC_REGEX = re.compile(r"<loc>\s*(https?://[^\s<]+)", re.IGNORECASE)

    @classmethod
    def parse_sitemap(cls, content: str) -> Tuple[List[SitemapUrl], List[str]]:
        urls: List[SitemapUrl] = []
        child_sitemaps: List[str] = []

        if not content or not content.strip():
            return urls, child_sitemaps

        cleaned_content = content.strip()

        if re.search(r"<!(?:DOCTYPE|ENTITY)\b", cleaned_content, re.IGNORECASE):
            return urls, child_sitemaps

        try:
            root = ET.fromstring(cleaned_content)
            tag_name = cls._strip_ns(root.tag).lower()

            if tag_name == "sitemapindex":
                for sitemap_elem in root:
                    if cls._strip_ns(sitemap_elem.tag).lower() == "sitemap":
                        loc = None
                        for child in sitemap_elem:
                            if cls._strip_ns(child.tag).lower() == "loc" and child.text:
                                loc = child.text.strip()
                                break
                        if loc:
                            child_sitemaps.append(loc)

            elif tag_name == "urlset":
                for url_elem in root:
                    if cls._strip_ns(url_elem.tag).lower() == "url":
                        loc = None
                        lastmod = None
                        changefreq = None
                        priority = None

                        for child in url_elem:
                            child_tag = cls._strip_ns(child.tag).lower()
                            text = child.text.strip() if child.text else None
                            if child_tag == "loc":
                                loc = text
                            elif child_tag == "lastmod":
                                lastmod = text
                            elif child_tag == "changefreq":
                                changefreq = text
                            elif child_tag == "priority" and text:
                                try:
                                    priority = float(text)
                                except ValueError:
                                    pass

                        if loc:
                            urls.append(
                                SitemapUrl(
                                    loc=loc,
                                    lastmod=lastmod,
                                    changefreq=changefreq,
                                    priority=priority,
                                )
                            )
            else:
                for elem in root.iter():
                    if cls._strip_ns(elem.tag).lower() == "loc" and elem.text:
                        loc_text = elem.text.strip()
                        if loc_text.startswith("http://") or loc_text.startswith("https://"):
                            urls.append(SitemapUrl(loc=loc_text))

            if not urls and not child_sitemaps:
                return cls._fallback_regex_parse(cleaned_content)

            return urls, child_sitemaps

        except ET.ParseError:
            return cls._fallback_regex_parse(cleaned_content)

    @classmethod
    def _strip_ns(cls, tag: str) -> str:
        return cls._NS_REGEX.sub("", tag)

    @classmethod
    def _fallback_regex_parse(cls, content: str) -> Tuple[List[SitemapUrl], List[str]]:
        urls: List[SitemapUrl] = []
        child_sitemaps: List[str] = []

        if re.search(r"<!(?:DOCTYPE|ENTITY)\b", content, re.IGNORECASE):
            return urls, child_sitemaps

        is_index = "<sitemapindex" in content.lower() or "<sitemap>" in content.lower()
        loc_matches = cls._URL_LOC_REGEX.findall(content)

        for loc in loc_matches:
            loc = loc.strip()
            if is_index:
                child_sitemaps.append(loc)
            else:
                urls.append(SitemapUrl(loc=loc))

        return urls, child_sitemaps


class SitemapDiscovery:
    """Manages multi-hop sitemap discovery with recursion ceilings."""

    def __init__(
        self,
        fetch_func: Callable[[str], str],
        max_sitemaps: int = 10,
        max_urls: int = 500,
    ) -> None:
        self.fetch_func = fetch_func
        self.max_sitemaps = max_sitemaps
        self.max_urls = max_urls

    def discover(self, seed_sitemaps: List[str]) -> List[SitemapUrl]:
        discovered_urls: List[SitemapUrl] = []
        visited_sitemaps: Set[str] = set()
        queue: deque[str] = deque(seed_sitemaps)

        while queue and len(visited_sitemaps) < self.max_sitemaps:
            sitemap_url = queue.popleft()
            if sitemap_url in visited_sitemaps:
                continue

            visited_sitemaps.add(sitemap_url)
            try:
                xml_text = self.fetch_func(sitemap_url)
                urls, child_indices = SitemapParser.parse_sitemap(xml_text)
                discovered_urls.extend(urls)

                for child in child_indices:
                    if child not in visited_sitemaps:
                        queue.append(child)

                if len(discovered_urls) >= self.max_urls:
                    discovered_urls = discovered_urls[: self.max_urls]
                    break

            except Exception:
                continue

        return discovered_urls


# ==============================================================================
# SECTION 9: STREAMING HTML PARSER
# ==============================================================================

COMMERCIAL_CTA_REGEX = re.compile(
    r"\b(buy|order|purchase|checkout|cart|subscribe|sign\s*up|get\s*started|start\s*free|try\s*free|book\s*demo|request\s*demo|contact\s*sales|get\s*quote|pricing|plans|pricing-plans|trial)\b",
    re.IGNORECASE,
)


class StreamingHTMLParser(HTMLParser):
    """Zero-dependency single-pass streaming HTML parser."""

    IGNORE_TAGS = {"script", "style", "noscript", "svg", "canvas", "template", "iframe"}
    LANDMARK_TAGS = {"main", "article", "header", "nav", "footer", "aside", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        self.title: str = ""
        self.language: Optional[str] = None
        self.canonical: Optional[str] = None
        self.canonicals: List[str] = []
        self.meta_tags: List[Dict[str, str]] = []
        self.meta_robots: List[str] = []

        self.headings: List[Heading] = []
        self.raw_links: List[Tuple[str, str, Optional[str]]] = []
        self.jsonld_blocks: List[Tuple[str, str, int]] = []
        self.semantic_landmarks: List[str] = []
        self.tables: List[TableData] = []
        self.code_blocks: List[str] = []
        self.images: List[Dict[str, str]] = []
        self.ctas: List[CTA] = []
        self.hreflangs: List[HreflangLink] = []
        self.feed_links: List[str] = []
        self.dates: Dict[str, Optional[str]] = {"published": None, "modified": None}
        self.authors: List[str] = []
        self._text_chunks: List[str] = []

        self._tag_stack: List[str] = []
        self._hidden_depth: int = 0
        self._hidden_tag_stack: List[str] = []
        self._current_location: str = "head"
        self._in_title: bool = False
        self._title_chunks: List[str] = []

        self._in_heading: bool = False
        self._current_heading_level: int = 0
        self._heading_chunks: List[str] = []

        self._in_link: bool = False
        self._current_link_href: str = ""
        self._current_link_rel: Optional[str] = None
        self._current_link_class: str = ""
        self._link_text_chunks: List[str] = []

        self._in_button: bool = False
        self._button_text_chunks: List[str] = []
        self._button_href: str = ""
        self._button_tag: str = "button"

        self._in_jsonld: bool = False
        self._jsonld_chunks: List[str] = []
        self._jsonld_index: int = 0

        self._in_code: bool = False
        self._code_chunks: List[str] = []

        self._in_table: bool = False
        self._in_th: bool = False
        self._in_td: bool = False
        self._cell_chunks: List[str] = []
        self._current_table_headers: List[str] = []
        self._current_table_rows: List[List[str]] = []
        self._current_table_row: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        self._tag_stack.append(tag_lower)
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower == "head":
            self._current_location = "head"
        elif tag_lower == "body":
            self._current_location = "body"

        if tag_lower == "html" and "lang" in attr_dict:
            self.language = attr_dict["lang"]

        if tag_lower in self.LANDMARK_TAGS and tag_lower not in self.semantic_landmarks:
            self.semantic_landmarks.append(tag_lower)

        style_val = attr_dict.get("style", "").lower().replace(" ", "")
        class_id_val = f"{attr_dict.get('class', '')} {attr_dict.get('id', '')}".lower()
        is_hidden_node = (
            "hidden" in attr_dict
            or attr_dict.get("aria-hidden", "").lower() == "true"
            or "display:none" in style_val
            or "visibility:hidden" in style_val
            or bool(re.search(r"\b(cookie|consent|onetrust|cc-banner|modal-hidden)\b", class_id_val))
        )
        if is_hidden_node:
            self._hidden_depth += 1
            self._hidden_tag_stack.append(tag_lower)

        if tag_lower == "meta":
            name = attr_dict.get("name") or attr_dict.get("property") or attr_dict.get("http-equiv") or ""
            content = attr_dict.get("content", "")
            if name or content:
                self.meta_tags.append({"name": name, "content": content})
            name_lower = name.lower()
            if name_lower in {"robots", "googlebot", "bingbot"}:
                directives = [d.strip().lower() for d in content.split(",") if d.strip()]
                self.meta_robots.extend(directives)
            elif name_lower in {"article:published_time", "pubdate", "datepublished", "date", "dc.date"}:
                if not self.dates["published"]:
                    self.dates["published"] = content
            elif name_lower in {"article:modified_time", "last-modified", "datemodified", "dc.date.modified"}:
                if not self.dates["modified"]:
                    self.dates["modified"] = content
            elif name_lower in {"author", "article:author", "dc.creator"}:
                if content and content not in self.authors:
                    self.authors.append(content)

        elif tag_lower == "link":
            rel = attr_dict.get("rel", "").lower().split()
            if "canonical" in rel:
                href = attr_dict.get("href", "").strip()
                if href:
                    self.canonicals.append(href)
                    if not self.canonical:
                        self.canonical = href
            if "alternate" in rel:
                hreflang = attr_dict.get("hreflang", "").strip()
                href = attr_dict.get("href", "").strip()
                if hreflang and href:
                    self.hreflangs.append(HreflangLink(lang=hreflang, href=href))
                type_val = attr_dict.get("type", "").lower()
                if any(x in type_val for x in ("rss", "atom", "xml")) and href and href not in self.feed_links:
                    self.feed_links.append(href)

        elif tag_lower == "title":
            self._in_title = True
            self._title_chunks = []

        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._in_heading = True
            self._current_heading_level = int(tag_lower[1])
            self._heading_chunks = []

        elif tag_lower == "button" or (tag_lower in ("div", "span") and attr_dict.get("role", "").lower() == "button"):
            self._in_button = True
            self._button_tag = tag_lower
            self._button_href = attr_dict.get("data-href") or attr_dict.get("href") or ""
            self._button_text_chunks = []

        elif tag_lower == "input":
            itype = attr_dict.get("type", "").lower()
            if itype in ("submit", "button"):
                val = (attr_dict.get("value") or attr_dict.get("aria-label") or "").strip()
                if val:
                    is_comm = bool(COMMERCIAL_CTA_REGEX.search(val))
                    self.ctas.append(CTA(text=val, href="", tag="input", is_commercial_cta=is_comm))

        elif tag_lower == "a":
            self._in_link = True
            self._current_link_href = attr_dict.get("href", "")
            self._current_link_rel = attr_dict.get("rel")
            self._current_link_class = attr_dict.get("class", "")
            self._link_text_chunks = []

        elif tag_lower == "img":
            src = attr_dict.get("src", "")
            alt = attr_dict.get("alt", "")
            if src or alt:
                self.images.append({
                    "src": src,
                    "alt": alt,
                    "class": attr_dict.get("class", ""),
                    "id": attr_dict.get("id", ""),
                })
            if alt:
                if self._in_link:
                    self._link_text_chunks.append(alt)
                if self._in_button:
                    self._button_text_chunks.append(alt)

        elif tag_lower == "script":
            script_type = attr_dict.get("type", "").lower()
            if script_type == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_chunks = []

        elif tag_lower in {"pre", "code"}:
            self._in_code = True
            self._code_chunks = []

        elif tag_lower == "table":
            self._in_table = True
            self._current_table_headers = []
            self._current_table_rows = []
        elif tag_lower == "tr" and self._in_table:
            self._current_table_row = []
        elif tag_lower == "th" and self._in_table:
            self._in_th = True
            self._cell_chunks = []
        elif tag_lower == "td" and self._in_table:
            self._in_td = True
            self._cell_chunks = []

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if self._tag_stack and self._tag_stack[-1] == tag_lower:
            self._tag_stack.pop()

        if self._hidden_tag_stack and self._hidden_tag_stack[-1] == tag_lower:
            self._hidden_tag_stack.pop()
            self._hidden_depth = max(0, self._hidden_depth - 1)

        if tag_lower == "title":
            self._in_title = False
            self.title = " ".join(self._title_chunks).strip()

        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._in_heading:
            self._in_heading = False
            heading_text = " ".join(self._heading_chunks).strip()
            if heading_text and self._hidden_depth == 0:
                self.headings.append(
                    Heading(level=self._current_heading_level, text=heading_text)
                )

        elif tag_lower in ("button", "div", "span") and self._in_button:
            self._in_button = False
            btn_text = " ".join(self._button_text_chunks).strip()
            if btn_text:
                is_comm = bool(COMMERCIAL_CTA_REGEX.search(btn_text))
                self.ctas.append(
                    CTA(text=btn_text, href=self._button_href, tag=self._button_tag, is_commercial_cta=is_comm)
                )

        elif tag_lower == "a" and self._in_link:
            self._in_link = False
            link_text = " ".join(self._link_text_chunks).strip()
            if self._current_link_href:
                self.raw_links.append(
                    (self._current_link_href, link_text, self._current_link_rel)
                )
                is_btn = bool(re.search(r"\b(btn|button|cta|action)\b", self._current_link_class, re.I))
                is_comm = bool(COMMERCIAL_CTA_REGEX.search(link_text))
                if (is_comm or is_btn) and link_text:
                    self.ctas.append(
                        CTA(text=link_text, href=self._current_link_href, tag="a", is_commercial_cta=is_comm)
                    )

        elif tag_lower == "script" and self._in_jsonld:
            self._in_jsonld = False
            json_text = "".join(self._jsonld_chunks).strip()
            if json_text:
                self.jsonld_blocks.append(
                    (json_text, self._current_location, self._jsonld_index)
                )
                self._jsonld_index += 1

        elif tag_lower in {"pre", "code"} and self._in_code:
            self._in_code = False
            code_text = "".join(self._code_chunks).strip()
            if code_text and len(code_text) > 10:
                self.code_blocks.append(code_text)

        elif tag_lower == "th" and self._in_th:
            self._in_th = False
            cell_text = " ".join(self._cell_chunks).strip()
            self._current_table_headers.append(cell_text)

        elif tag_lower == "td" and self._in_td:
            self._in_td = False
            cell_text = " ".join(self._cell_chunks).strip()
            self._current_table_row.append(cell_text)

        elif tag_lower == "tr" and self._in_table:
            if self._current_table_row:
                self._current_table_rows.append(self._current_table_row)

        elif tag_lower == "table" and self._in_table:
            self._in_table = False
            if self._current_table_headers or self._current_table_rows:
                self.tables.append(
                    TableData(
                        headers=self._current_table_headers,
                        rows=self._current_table_rows,
                    )
                )

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_chunks.append(data)
        if self._in_heading:
            self._heading_chunks.append(data)
        if self._in_link:
            self._link_text_chunks.append(data)
        if self._in_button:
            self._button_text_chunks.append(data)
        if self._in_jsonld:
            self._jsonld_chunks.append(data)
        if self._in_code:
            self._code_chunks.append(data)
        if self._in_th or self._in_td:
            self._cell_chunks.append(data)

        if (
            self._current_location == "body"
            and not self._in_title
            and not self._in_code
            and not self._in_th
            and not self._in_td
            and self._hidden_depth == 0
            and not any(t in self.IGNORE_TAGS for t in self._tag_stack)
        ):
            self._text_chunks.append(data)

    def get_accumulated_text(self) -> str:
        raw_text = " ".join(self._text_chunks)
        return " ".join(raw_text.split())

    def parse_http_headers(self, headers: Dict[str, str]) -> List[str]:
        x_robots: List[str] = []
        if not headers:
            return x_robots
        for k, v in headers.items():
            k_lower = k.lower()
            if k_lower == "x-robots-tag":
                directives = [d.strip().lower() for d in v.split(",") if d.strip()]
                x_robots.extend(directives)
                self.meta_robots.extend(directives)
            elif k_lower == "link":
                m = re.search(r'<([^>]+)>;\s*rel=["\']?canonical["\']?', v, re.IGNORECASE)
                if m:
                    c_url = m.group(1).strip()
                    if c_url:
                        self.canonicals.append(c_url)
                        if not self.canonical:
                            self.canonical = c_url
            elif k_lower == "last-modified" and not self.dates["modified"]:
                self.dates["modified"] = v.strip()
        return x_robots


# ==============================================================================
# SECTION 10: METADATA & LINK PROCESSORS
# ==============================================================================

class MetadataProcessor:
    """Normalizes raw HTML meta tags into structured OpenGraph, Twitter, and indexer directives."""

    @classmethod
    def process_metadata(
        cls, meta_tags: List[Dict[str, str]], source_url: str = ""
    ) -> Tuple[Dict[str, Any], List[Observation]]:
        structured: Dict[str, Any] = {
            "standard": {},
            "opengraph": {},
            "twitter": {},
            "dublin_core": {},
            "robots_directives": [],
        }
        observations: List[Observation] = []

        for item in meta_tags:
            name = item.get("name", "").strip().lower()
            content = item.get("content", "").strip()
            if not name or not content:
                continue

            if name in {"robots", "googlebot", "bingbot"}:
                directives = [d.strip().lower() for d in content.split(",") if d.strip()]
                structured["robots_directives"].extend(directives)

                if "nosnippet" in directives:
                    observations.append(
                        Observation(
                            type="indexer_restriction",
                            value="nosnippet_detected",
                            confidence="high",
                            evidence=f"Meta tag '{name}' contains 'nosnippet' directive on {source_url}",
                            severity_hint="critical",
                        )
                    )
                if "noindex" in directives:
                    observations.append(
                        Observation(
                            type="indexer_restriction",
                            value="noindex_detected",
                            confidence="high",
                            evidence=f"Meta tag '{name}' contains 'noindex' directive on {source_url}",
                            severity_hint="critical",
                        )
                    )

            elif name.startswith("og:"):
                structured["opengraph"][name[3:]] = content
            elif name.startswith("twitter:"):
                structured["twitter"][name[8:]] = content
            elif name.startswith("dc.") or name.startswith("dc:"):
                structured["dublin_core"][name[3:]] = content
            else:
                structured["standard"][name] = content

        return structured, observations


IGNORED_EXTENSIONS: Set[str] = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css", ".js",
    ".mjs", ".zip", ".tar", ".gz", ".rar", ".7z", ".mp4", ".webm", ".avi", ".mov",
    ".mp3", ".wav", ".ogg", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".xml",
    ".json", ".txt", ".csv", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}

NON_HTTP_SCHEMES: Set[str] = {"mailto", "tel", "javascript", "data", "whatsapp", "sms"}

TRACKING_PARAMS: Set[str] = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "ref", "source",
    "_hsenc", "_hsmi", "hsCtaTracking", "session_id", "sid",
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

        port = parsed.port
        netloc = host
        if port and not (scheme == "http" and port == 80) and not (scheme == "https" and port == 443):
            netloc = f"{host}:{port}"

        path = parsed.path or "/"
        while "//" in path:
            path = path.replace("//", "/")

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
            if target_host.endswith("." + base_host):
                return True
            if base_host.startswith("www.") and base_host[4:] == target_host:
                return True
            if target_host.startswith("www.") and target_host[4:] == base_host:
                return True

        return False

    @classmethod
    def is_crawlable_html_url(cls, url: str) -> bool:
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

        full_query = parsed.path + ("?" + parsed.query if parsed.query else "")
        if UNSAFE_PATH_REGEX.search(unquote(full_query)):
            return False

        return all(not re.search(pattern, path) for pattern in JUNK_PATH_PATTERNS)

    @classmethod
    def resolve_and_filter_links(
        cls,
        base_url: str,
        raw_links: List[Tuple[str, str, Optional[str]]],
        allow_subdomains: bool = False,
    ) -> List[Link]:
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
    p = urlsplit(url)
    full = unquote(p.path + ("?" + p.query if p.query else ""))
    return not bool(UNSAFE_PATH_REGEX.search(full))


def normalize(url: str) -> str:
    """Normalize public HTTP/HTTPS URL per strict safety contract."""
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
    is_default_port = (p.scheme == "https" and p.port == 443) or (p.scheme == "http" and p.port == 80)
    netloc = host + (f":{p.port}" if p.port and not is_default_port else "")
    return urlunsplit((
        p.scheme,
        netloc,
        quote(p.path or "/", safe="/%:@!$&'()*+,;=-._~"),
        quote(p.query, safe="%=&/?@:!$'()*+,;~-._"),
        "",
    ))


# ==============================================================================
# SECTION 11: JSON-LD SCHEMA EXTRACTOR
# ==============================================================================

class JsonLdExtractor:
    """Parses and normalizes Schema.org JSON-LD scripts with provenance tracking."""

    @classmethod
    def parse_blocks(
        cls,
        raw_blocks: List[Tuple[str, str, int]],
        source_url: str = "",
    ) -> Tuple[List[Dict[str, Any]], List[FactCandidate], List[Observation]]:
        schemas: List[Dict[str, Any]] = []
        facts: List[FactCandidate] = []
        observations: List[Observation] = []

        if not raw_blocks:
            observations.append(
                Observation(
                    type="schema_gap",
                    value="no_jsonld_structured_data_found",
                    confidence="high",
                    evidence=f"No <script type='application/ld+json'> blocks found on {source_url}",
                    severity_hint="high",
                )
            )
            return schemas, facts, observations

        for raw_text, location, block_idx in raw_blocks:
            clean_text = raw_text.strip()
            if not clean_text:
                continue

            try:
                parsed_data = json.loads(clean_text)
            except json.JSONDecodeError as e:
                observations.append(
                    Observation(
                        type="schema_syntax_error",
                        value="jsonld_parse_failure",
                        confidence="high",
                        evidence=f"Block #{block_idx} ({location}) failed to parse as JSON: {e}",
                        severity_hint="high",
                    )
                )
                continue

            flattened = cls._flatten_jsonld(parsed_data)
            for item in flattened:
                if isinstance(item, dict):
                    item["_provenance"] = {
                        "block_index": block_idx,
                        "location": location,
                        "source_url": source_url,
                    }
                    schemas.append(item)
                    cls._extract_facts_from_schema(item, source_url, block_idx, facts)

        return schemas, facts, observations

    @classmethod
    def _flatten_jsonld(cls, data: Any, visited: Optional[Set[int]] = None) -> List[Dict[str, Any]]:
        if visited is None:
            visited = set()
        data_id = id(data)
        if data_id in visited:
            return []
        visited.add(data_id)

        results: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for element in data:
                results.extend(cls._flatten_jsonld(element, visited))
        elif isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                if "@type" in data:
                    results.append({k: v for k, v in data.items() if k != "@graph"})
                for element in data["@graph"]:
                    results.extend(cls._flatten_jsonld(element, visited))
            else:
                results.append(data)
        return results

    @classmethod
    def _extract_facts_from_schema(
        cls,
        schema: Dict[str, Any],
        source_url: str,
        block_idx: int,
        facts: List[FactCandidate],
    ) -> None:
        schema_type = schema.get("@type")
        if not schema_type:
            return

        type_names = [schema_type] if isinstance(schema_type, str) else schema_type

        # Organization facts
        if any("Organization" in t or "Corporation" in t for t in type_names):
            org_name = schema.get("name")
            if org_name:
                facts.append(
                    FactCandidate(
                        attribute="entity_name",
                        value=org_name,
                        entity=org_name,
                        source_url=source_url,
                        locator=f"[{block_idx}].Organization.name",
                        mechanism="jsonld",
                    )
                )

            telephone = schema.get("telephone")
            if telephone:
                facts.append(
                    FactCandidate(
                        attribute="phone",
                        value=str(telephone).strip(),
                        entity=org_name,
                        source_url=source_url,
                        locator=f"[{block_idx}].Organization.telephone",
                        mechanism="jsonld",
                    )
                )

            email = schema.get("email")
            if email:
                facts.append(
                    FactCandidate(
                        attribute="email",
                        value=str(email).strip(),
                        entity=org_name,
                        source_url=source_url,
                        locator=f"[{block_idx}].Organization.email",
                        mechanism="jsonld",
                    )
                )

        # Product & Offer facts
        if any("Product" in t for t in type_names):
            prod_name = schema.get("name", "")
            offers = schema.get("offers")
            offer_list: List[Dict[str, Any]] = []
            if isinstance(offers, dict):
                offer_list = [offers]
            elif isinstance(offers, list):
                offer_list = [o for o in offers if isinstance(o, dict)]

            for o_idx, offer in enumerate(offer_list):
                price = offer.get("price")
                currency = offer.get("priceCurrency")
                if price is not None:
                    try:
                        clean_price = float(str(price).replace(",", "").replace("$", "").strip())
                    except ValueError:
                        clean_price = price

                    facts.append(
                        FactCandidate(
                            attribute="price",
                            value=clean_price,
                            currency=str(currency).upper() if currency else None,
                            entity=prod_name or "Product",
                            source_url=source_url,
                            locator=f"[{block_idx}].Product.offers[{o_idx}].price",
                            mechanism="jsonld",
                        )
                    )


# ==============================================================================
# SECTION 12: EVIDENCE & CONTENT EXTRACTOR
# ==============================================================================

class EvidenceExtractor:
    """Extracts structured facts, clean Markdown, and epistemic observations from HTML."""

    CURRENCY_MAP = {
        "$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR", "£": "GBP",
        "GBP": "GBP", "¥": "JPY", "JPY": "JPY", "₹": "INR", "INR": "INR",
    }

    INTERVAL_MAP = {
        "mo": "monthly", "month": "monthly", "yr": "yearly", "year": "yearly",
        "user": "per_user", "day": "daily", "week": "weekly",
    }

    PRICE_REGEX = re.compile(
        r"(?P<currency>[\$\€\£\¥\₹]|USD|EUR|GBP|JPY|INR)\s*(?P<amount>\d{1,6}(?:,\d{3})*(?:\.\d{2})?)\s*(?:/(?P<interval>mo|month|yr|year|user|day|week))?",
        re.IGNORECASE,
    )
    PHONE_REGEX = re.compile(
        r"(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{2,9}"
    )
    EMAIL_REGEX = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )
    STAT_REGEX = re.compile(
        r"\b(?:\d{1,3}(?:\.\d+)?%|\d+(?:\.\d+)?x|\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b"
    )
    CAUSAL_CONNECTORS = [
        "because", "due to", "as a result of", "which leads to",
        "which enables", "consequently", "therefore", "resulting in",
    ]

    SPA_SHELL_INDICATORS = [
        r'<div\s+id=["\'](?:root|app|__next)["\']>\s*</div>',
        r'<div\s+id=["\']root["\']\s*/>',
        r'<div\s+id=["\']app["\']\s*/>',
        r'You need to enable JavaScript to run this app',
    ]

    @classmethod
    def strip_boilerplate(cls, raw_html: str) -> str:
        if not raw_html:
            return ""

        text = raw_html
        for tag in ["script", "style", "noscript", "svg", "header", "nav", "footer", "aside", "template"]:
            text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", text, flags=re.IGNORECASE | re.DOTALL)

        text = re.sub(r"<([a-zA-Z0-9]+)[^>]*?\b(?:hidden|aria-hidden=['\"]true['\"])[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<([a-zA-Z0-9]+)[^>]*?style=['\"][^'\"]*?display:\s*none[^'\"]*?['\"][^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<([a-zA-Z0-9]+)[^>]*?(?:class|id)=['\"][^'\"]*?(?:cookie|consent|onetrust)[^'\"]*?['\"][^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(clean_lines)

    @classmethod
    def calculate_text_density_ratio(cls, clean_text: str, raw_html: str) -> float:
        html_bytes = len(raw_html.encode("utf-8"))
        if html_bytes == 0:
            return 0.0
        clean_bytes = len(clean_text.encode("utf-8"))
        return round(clean_bytes / float(html_bytes), 4)

    calculate_snr = calculate_text_density_ratio

    @classmethod
    def detect_rendering_limitations(
        cls, raw_html: str, clean_text: str, source_url: str
    ) -> List[Observation]:
        observations: List[Observation] = []
        word_count = len(clean_text.split())
        html_size = len(raw_html)

        is_empty_spa = any(re.search(pat, raw_html, re.IGNORECASE) for pat in cls.SPA_SHELL_INDICATORS)

        if is_empty_spa and word_count < 60:
            observations.append(
                Observation(
                    type="rendering_observation",
                    value="server_html_appears_sparse",
                    confidence="high",
                    evidence=(
                        f"Target {source_url} returns an empty SPA shell "
                        f"({word_count} visible words, HTML size {html_size} bytes). "
                        "Critical content is likely client-side rendered via JavaScript."
                    ),
                    severity_hint="critical",
                )
            )
        elif html_size > 30000 and word_count < 40:
            observations.append(
                Observation(
                    type="rendering_observation",
                    value="server_html_appears_sparse",
                    confidence="medium",
                    evidence=(
                        f"Heavy HTML envelope ({html_size} bytes) on {source_url} yielded only "
                        f"{word_count} visible words, suggesting client-side hydration dependency."
                    ),
                    severity_hint="high",
                )
            )

        return observations

    @classmethod
    def build_clean_markdown(
        cls,
        title: str,
        headings: List[Heading],
        clean_text: str,
        tables: List[TableData],
        code_blocks: List[str],
    ) -> str:
        md_parts: List[str] = []

        if title:
            md_parts.append(f"# {title}\n")

        for idx, table in enumerate(tables, 1):
            if table.headers or table.rows:
                md_parts.append(f"### Table {idx}")
                if table.headers:
                    md_parts.append("| " + " | ".join(table.headers) + " |")
                    md_parts.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
                for row in table.rows:
                    md_parts.append("| " + " | ".join(row) + " |")
                md_parts.append("")

        for block in code_blocks:
            md_parts.append("```\n" + block + "\n```\n")

        if clean_text:
            md_parts.append("## Main Content\n")
            md_parts.append(clean_text)

        return "\n".join(md_parts)

    @classmethod
    def extract_facts_and_claims(
        cls, clean_text: str, source_url: str
    ) -> Tuple[List[FactCandidate], List[ClaimCandidate]]:
        facts: List[FactCandidate] = []
        claims: List[ClaimCandidate] = []

        if not clean_text:
            return facts, claims

        # Price facts
        for match in cls.PRICE_REGEX.finditer(clean_text):
            try:
                raw_amt = match.group("amount").replace(",", "")
                price_val = float(raw_amt)
                raw_curr = match.group("currency")
                currency = cls.CURRENCY_MAP.get(raw_curr.upper(), raw_curr) if raw_curr else "USD"
                raw_interval = match.group("interval")
                interval = cls.INTERVAL_MAP.get(raw_interval.lower(), raw_interval) if raw_interval else "one_time"
                facts.append(
                    FactCandidate(
                        attribute="price",
                        value=price_val,
                        currency=currency,
                        interval=interval,
                        source_url=source_url,
                        locator="visible_text",
                        mechanism="visible_text",
                    )
                )
            except (ValueError, AttributeError):
                pass

        # Contact facts
        for match in cls.EMAIL_REGEX.finditer(clean_text):
            facts.append(
                FactCandidate(
                    attribute="email",
                    value=match.group(0),
                    source_url=source_url,
                    locator="visible_text",
                    mechanism="visible_text",
                )
            )

        for match in cls.PHONE_REGEX.finditer(clean_text):
            phone_str = match.group(0).strip()
            digits_only = re.sub(r"\D", "", phone_str)
            if 7 <= len(digits_only) <= 15:
                facts.append(
                    FactCandidate(
                        attribute="phone",
                        value=phone_str,
                        source_url=source_url,
                        locator="visible_text",
                        mechanism="visible_text",
                    )
                )

        t_claims = clean_text
        abbr_repls = [("e.g.", "__EG__"), ("i.e.", "__IE__"), ("Dr.", "__DR__"), ("vs.", "__VS__"), ("Ph.D.", "__PHD__")]
        for a, tok in abbr_repls:
            if a in t_claims:
                t_claims = t_claims.replace(a, tok)
        raw_sents = re.split(r"[.!?]+(?:\s+|$)", t_claims)
        sentences = []
        for s in raw_sents:
            for a, tok in abbr_repls:
                if tok in s:
                    s = s.replace(tok, a)
            s_clean = s.strip()
            if len(s_clean) > 25:
                sentences.append(s_clean)
        for sent in sentences:
            has_stat = bool(cls.STAT_REGEX.search(sent))
            causal_hit = next((conn for conn in cls.CAUSAL_CONNECTORS if conn in sent.lower()), None)

            if has_stat or causal_hit:
                claims.append(
                    ClaimCandidate(
                        claim_text=sent,
                        causal_type=causal_hit,
                        statistical_proposition=has_stat,
                        source_url=source_url,
                    )
                )

        return facts, claims

    SOCIAL_DOMAINS = (
        "linkedin.com", "github.com", "twitter.com", "x.com", "youtube.com",
        "facebook.com", "instagram.com", "discord.gg", "discord.com", "medium.com",
    )

    @classmethod
    def extract_contact_and_social_info(
        cls, clean_text: str, links: List[Any]
    ) -> Tuple[Dict[str, List[str]], List[str]]:
        contact_info: Dict[str, List[str]] = {"emails": [], "phones": []}
        social_links: List[str] = []

        if clean_text:
            for match in cls.EMAIL_REGEX.finditer(clean_text):
                em = match.group(0).lower()
                if em not in contact_info["emails"]:
                    contact_info["emails"].append(em)

            for match in cls.PHONE_REGEX.finditer(clean_text):
                ph = match.group(0).strip()
                digits = re.sub(r"\D", "", ph)
                if 7 <= len(digits) <= 15 and ph not in contact_info["phones"]:
                    contact_info["phones"].append(ph)

        if links:
            seen_social = set()
            for link in links:
                if isinstance(link, (tuple, list)) and len(link) > 0:
                    href = str(link[0] or "")
                elif hasattr(link, "href"):
                    href = str(link.href or "")
                elif isinstance(link, dict):
                    href = str(link.get("href") or "")
                else:
                    href = str(link or "")
                m = re.search(r"https?://[^\s'\"\)]+", href)
                if m:
                    href = m.group(0)
                href_lower = (href or "").lower()
                if any(dom in href_lower for dom in cls.SOCIAL_DOMAINS) and href not in seen_social and href.startswith(("http://", "https://")):
                    seen_social.add(href)
                    social_links.append(href)

        return contact_info, social_links


# ==============================================================================
# SECTION 13: MASTER WEBAUDITENGINE
# ==============================================================================

class WebAuditEngine:
    """Master web acquisition orchestrator and agent-facing retrieval interface."""

    def __init__(
        self,
        time_limit_sec: float = 120.0,
        max_pages: int = 25,
        max_depth: int = 3,
        max_concurrency: int = 6,
        user_agent: Optional[str] = None,
        allow_private_ips: bool = False,
        strict_robots: bool = False,
    ) -> None:
        self.max_depth = max_depth
        self.strict_robots = strict_robots
        self.budget = Budget(
            time_limit_sec=time_limit_sec,
            max_pages=max_pages,
            max_depth=max_depth,
            max_concurrency=max_concurrency,
        )
        self.policy = SecurityPolicy(allow_private_ips=allow_private_ips)
        self.fetcher = SafeFetcher(
            policy=self.policy, budget=self.budget, user_agent=user_agent
        )
        self.frontier = Frontier(max_capacity=1000)

        # Audit state
        self.site_url: str = ""
        self.robots_auditor: Optional[RobotsAuditor] = None
        self.pages: List[PageModel] = []
        self.observations: List[Observation] = []
        self.all_facts: List[FactCandidate] = []
        self.all_claims: List[ClaimCandidate] = []
        self.llms_txt_content: Optional[str] = None
        self.llms_full_txt_content: Optional[str] = None
        self.pricing_manifest_content: Optional[str] = None
        self.pricing_manifest_status: int = 404
        self.ai_plugin_content: Optional[str] = None
        self.ai_plugin_status: int = 404
        self.security_txt_content: Optional[str] = None
        self.security_txt_status: int = 404
        self.nav_fragment_content: Optional[str] = None
        self.nav_fragment_url: Optional[str] = None
        self.nav_fragment_links: List[str] = []

    def crawl(self, seed_url: str) -> EvidenceModel:
        norm_seed = LinkProcessor.normalize_url(seed_url)
        if not norm_seed:
            raise ValueError(f"Invalid seed URL: {seed_url}")

        self.site_url = norm_seed
        parsed = urlparse(self.site_url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        # 1. Discover & Audit robots.txt
        robots_url = urljoin(base_origin, "/robots.txt")
        declared_sitemaps: List[str] = []
        try:
            robots_res = self.fetcher.fetch(robots_url, timeout=5.0)
            robots_content = robots_res.body_bytes.decode("utf-8", errors="replace")
            if robots_res.status == 200:
                outcome = RobotsOutcome.OK
            elif robots_res.status == 404:
                outcome = RobotsOutcome.NOT_FOUND
            elif robots_res.status in (401, 403):
                outcome = RobotsOutcome.BLOCKED
            elif robots_res.status == 429 or robots_res.status >= 500:
                outcome = RobotsOutcome.SERVER_ERROR
            else:
                outcome = RobotsOutcome.SERVER_ERROR

            self.robots_auditor = RobotsAuditor(
                content=robots_content,
                status_code=robots_res.status,
                outcome=outcome,
            )
            declared_sitemaps = self.robots_auditor.sitemaps
        except Exception:
            self.robots_auditor = RobotsAuditor(
                content="", status_code=500, outcome=RobotsOutcome.SERVER_ERROR
            )

        # Strict robots check: abort if entrypoint disallowed
        if self.strict_robots and self.robots_auditor and not self.robots_auditor.is_allowed("*", self.site_url):
            self.observations.append(
                Observation(
                    type="crawler_access",
                    value="strict_robots_aborted",
                    confidence="high",
                    evidence=f"robots.txt disallows crawler access to seed URL {self.site_url}",
                    severity_hint="critical",
                )
            )
            return self._build_evidence_aggregate()

        # 2. Always fetch and process seed page first to guarantee primary inventory acquisition
        seed_page = self._fetch_and_process_page(self.site_url, depth=0)
        if seed_page:
            self.pages.append(seed_page)
            self.observations.extend(seed_page.observations)
            self.all_facts.extend(seed_page.facts)
            self.all_claims.extend(seed_page.claims)
            for link in seed_page.links:
                if link.is_internal and LinkProcessor.is_crawlable_html_url(link.href):
                    self.frontier.push(link.href, depth=1, source_url=self.site_url)

        # 3. Probe AI discovery manifests
        try:
            llms_res = self.fetcher.fetch(urljoin(base_origin, "/llms.txt"), timeout=3.0)
            if llms_res.status == 200:
                self.llms_txt_content = llms_res.body_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass

        try:
            llms_full_res = self.fetcher.fetch(urljoin(base_origin, "/llms-full.txt"), timeout=3.0)
            if llms_full_res.status == 200:
                self.llms_full_txt_content = llms_full_res.body_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass

        try:
            pricing_res = self.fetcher.fetch(urljoin(base_origin, "/pricing.md"), timeout=3.0)
            self.pricing_manifest_status = pricing_res.status
            if pricing_res.status == 200:
                self.pricing_manifest_content = pricing_res.body_bytes.decode("utf-8", errors="replace")
            else:
                pt_res = self.fetcher.fetch(urljoin(base_origin, "/pricing.txt"), timeout=3.0)
                self.pricing_manifest_status = pt_res.status
                if pt_res.status == 200:
                    self.pricing_manifest_content = pt_res.body_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass

        try:
            sec_res = self.fetcher.fetch(urljoin(base_origin, "/.well-known/security.txt"), timeout=3.0)
            self.security_txt_status = sec_res.status
            if sec_res.status == 200:
                self.security_txt_content = sec_res.body_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass

        try:
            plugin_res = self.fetcher.fetch(urljoin(base_origin, "/.well-known/ai-plugin.json"), timeout=3.0)
            self.ai_plugin_status = plugin_res.status
            if plugin_res.status == 200:
                self.ai_plugin_content = plugin_res.body_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass

        # 4. Probe dynamic navigation fragments (Adobe EDS, JAMstack, Headless CMS)
        for frag_path in ("/nav.plain.html", "/header.plain.html"):
            try:
                frag_url = urljoin(base_origin, frag_path)
                frag_res = self.fetcher.fetch(frag_url, timeout=3.0)
                if frag_res.status == 200 and frag_res.body_bytes:
                    self.nav_fragment_url = frag_url
                    self.nav_fragment_content = frag_res.body_bytes.decode("utf-8", errors="replace")
                    nav_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', self.nav_fragment_content, re.I)
                    for raw_h in nav_hrefs:
                        if raw_h.startswith(("#", "javascript:", "mailto:", "tel:")):
                            continue
                        full_nav_u = urljoin(base_origin, raw_h)
                        norm_nav_u = LinkProcessor.normalize_url(full_nav_u)
                        if norm_nav_u and LinkProcessor.is_same_origin(base_origin, norm_nav_u):
                            if norm_nav_u not in self.nav_fragment_links:
                                self.nav_fragment_links.append(norm_nav_u)
                            self.frontier.push(norm_nav_u, depth=1, is_sitemap_declared=False, source_url=frag_url)
                    break
            except Exception:
                pass

        # 5. Discover XML sitemaps
        sitemap_discovery = SitemapDiscovery(
            fetch_func=lambda u: self.fetcher.fetch(u, timeout=5.0).body_bytes.decode("utf-8", errors="replace"),
            max_sitemaps=6,
            max_urls=200,
        )
        sitemap_seed_list = declared_sitemaps or [urljoin(base_origin, "/sitemap.xml")]
        sitemap_urls = sitemap_discovery.discover(sitemap_seed_list)

        # 5. Populate frontier with sitemap URLs
        for sm_url in sitemap_urls:
            norm_sm = LinkProcessor.normalize_url(sm_url.loc)
            if norm_sm and LinkProcessor.is_same_origin(base_origin, norm_sm) and LinkProcessor.is_crawlable_html_url(norm_sm):
                self.frontier.push(norm_sm, depth=1, is_sitemap_declared=True)

        # 6. Core crawl loop
        while not self.frontier.is_empty() and self.budget.can_fetch_page():
            item = self.frontier.pop()
            if not item:
                break

            if self.budget.remaining_time() <= 1.0:
                break

            # Check robots permission
            if self.robots_auditor and not self.robots_auditor.is_allowed("OAI-SearchBot", item.url):
                self.observations.append(
                    Observation(
                        type="crawler_access",
                        value="ai_crawler_disallowed",
                        confidence="high",
                        evidence=f"robots.txt disallows OAI-SearchBot on {item.url}",
                        severity_hint="high",
                    )
                )

            page = self._fetch_and_process_page(item.url, depth=item.depth)
            if page:
                self.pages.append(page)
                self.observations.extend(page.observations)
                self.all_facts.extend(page.facts)
                self.all_claims.extend(page.claims)

                if item.depth < self.max_depth:
                    for link in page.links:
                        if link.is_internal and LinkProcessor.is_crawlable_html_url(link.href):
                            self.frontier.push(link.href, depth=item.depth + 1, source_url=item.url)

        return self._build_evidence_aggregate()

    def _fetch_and_process_page(self, url: str, depth: int = 0) -> Optional[PageModel]:
        if not self.budget.reserve_page_slot(depth=depth):
            return None

        try:
            resource = self.fetcher.fetch(url, timeout=10.0)
            if not resource.content_type.startswith("text/html") and not resource.content_type.startswith("application/xhtml"):
                self.budget.release_page_slot()
                return None

            html_text = resource.body_bytes.decode("utf-8", errors="replace")

            parser = StreamingHTMLParser()
            parser.parse_http_headers(resource.headers)
            parser.feed(html_text)
            parser.close()

            clean_text = parser.get_accumulated_text()
            if not clean_text or len(clean_text) < 100:
                clean_text = EvidenceExtractor.strip_boilerplate(html_text)

            word_count = len(clean_text.split())
            snr = EvidenceExtractor.calculate_text_density_ratio(clean_text, html_text)

            clean_md = EvidenceExtractor.build_clean_markdown(
                title=parser.title,
                headings=parser.headings,
                clean_text=clean_text,
                tables=parser.tables,
                code_blocks=parser.code_blocks,
            )

            is_valid_canon, canon_obs = CanonicalValidator.evaluate(resource.final_url, parser.canonical)
            meta_struct, meta_obs = MetadataProcessor.process_metadata(parser.meta_tags, source_url=resource.final_url)
            schemas, jsonld_facts, jsonld_obs = JsonLdExtractor.parse_blocks(parser.jsonld_blocks, source_url=resource.final_url)
            text_facts, text_claims = EvidenceExtractor.extract_facts_and_claims(clean_text, source_url=resource.final_url)
            rendering_obs = EvidenceExtractor.detect_rendering_limitations(html_text, clean_text, source_url=resource.final_url)
            contact_info, social_links = EvidenceExtractor.extract_contact_and_social_info(clean_text, parser.raw_links)

            resolved_links = LinkProcessor.resolve_and_filter_links(resource.final_url, parser.raw_links)
            heading_texts = [h.text for h in parser.headings]
            page_type = PageClassifier.classify(
                url=resource.final_url,
                title=parser.title,
                schemas=schemas,
                headings=heading_texts,
            )

            all_page_obs = canon_obs + meta_obs + jsonld_obs + rendering_obs
            if resource.status in (404, 410):
                all_page_obs.append(
                    Observation(
                        type="broken_link",
                        value=f"http_status_{resource.status}",
                        confidence="high",
                        evidence=f"Internal link returned HTTP {resource.status}: {resource.url}",
                        severity_hint="high",
                    )
                )
            elif resource.status >= 400:
                all_page_obs.append(
                    Observation(
                        type="http_error",
                        value=f"http_status_{resource.status}",
                        confidence="high",
                        evidence=f"HTTP {resource.status} returned for {resource.url}",
                        severity_hint="medium",
                    )
                )
            all_page_facts = jsonld_facts + text_facts

            self.budget.commit_page_slot()

            return PageModel(
                url=resource.url,
                final_url=resource.final_url,
                status=resource.status,
                content_type=resource.content_type,
                title=parser.title,
                description=meta_struct.get("standard", {}).get("description", ""),
                canonical=parser.canonical,
                canonicals=parser.canonicals,
                robots_meta=parser.meta_robots,
                language=parser.language,
                headings=parser.headings,
                links=resolved_links,
                ctas=parser.ctas,
                hreflangs=parser.hreflangs,
                social_links=social_links,
                contact_info=contact_info,
                dates=parser.dates,
                x_robots_tag=parser.meta_robots,
                redirect_chain=resource.redirects,
                jsonld=schemas,
                metadata=meta_struct,
                clean_text=clean_text,
                clean_markdown=clean_md,
                word_count=word_count,
                snr=snr,
                page_type=page_type,
                semantic_landmarks=parser.semantic_landmarks,
                tables=parser.tables,
                code_blocks=parser.code_blocks,
                images=parser.images,
                observations=all_page_obs,
                facts=all_page_facts,
                claims=text_claims,
                fetch_telemetry={
                    "latency_ms": resource.latency_ms,
                    "ip_address": resource.ip_address,
                    "bytes": len(resource.body_bytes),
                },
                headers=resource.headers,
                raw_html=html_text,
                truncated=resource.truncated,
            )

        except Exception:
            self.budget.release_page_slot()
            return None

    def _build_evidence_aggregate(self) -> EvidenceModel:
        entities: Dict[str, Any] = {}
        for f in self.all_facts:
            if f.entity:
                entities.setdefault(f.entity, {})[f.attribute] = f.value

        scrapeability = {
            "total_pages": len(self.pages),
            "pages_with_schema": sum(1 for p in self.pages if p.jsonld),
            "pages_with_canonical": sum(1 for p in self.pages if p.canonical),
            "average_word_count": (
                round(sum(p.word_count for p in self.pages) / max(1, len(self.pages)), 1)
            ),
            "average_snr": (
                round(sum(p.snr for p in self.pages) / max(1, len(self.pages)), 4)
            ),
            "sparse_render_count": sum(
                1 for obs in self.observations if obs.value == "server_html_appears_sparse"
            ),
        }

        return EvidenceModel(
            site=self.site_url,
            crawled_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            pages=self.pages,
            observations=self.observations,
            facts=self.all_facts,
            claims=self.all_claims,
            entities=entities,
            scrapeability_summary=scrapeability,
        )

    def to_inventory_dict(self) -> Dict[str, Any]:
        """Serializes current audit state to the canonical inv.json format required by all downstream sensors."""
        pages_data = []
        for p in self.pages:
            landmarks_dict = {
                "has_main": "main" in p.semantic_landmarks,
                "has_article": "article" in p.semantic_landmarks,
                "has_header": "header" in p.semantic_landmarks,
                "has_nav": "nav" in p.semantic_landmarks,
                "has_footer": "footer" in p.semantic_landmarks,
            }
            pages_data.append({
                "url": p.url,
                "final_url": p.final_url,
                "status": p.status,
                "resource_type": "html",
                "content_type": p.content_type,
                "page_type": p.page_type.get("value", "general") if isinstance(p.page_type, dict) else str(p.page_type),
                "page_type_confidence": p.page_type.get("confidence", 0.5) if isinstance(p.page_type, dict) else 0.5,
                "title": p.title,
                "description": p.description,
                "canonical": p.canonical,
                "canonicals": p.canonicals,
                "robots_meta": p.robots_meta,
                "headings": [h.to_dict() for h in p.headings],
                "links": [link.to_dict() for link in p.links],
                "ctas": [c.to_dict() for c in p.ctas],
                "social_links": p.social_links,
                "contact_info": p.contact_info,
                "word_count": p.word_count,
                "clean_text": p.clean_text,
                "clean_markdown": p.clean_markdown,
                "snr": p.snr,
                "text_density_ratio": p.snr,
                "semantic_landmarks": landmarks_dict,
                "semantic_landmarks_list": p.semantic_landmarks,
                "jsonld": p.jsonld,
                "metadata": p.metadata,
                "tables": [t.to_dict() for t in p.tables],
                "code_blocks": p.code_blocks,
                "images": p.images,
                "observations": [o.to_dict() for o in p.observations],
                "facts": [f.to_dict() for f in p.facts],
                "claims": [c.to_dict() for c in p.claims],
                "headers": p.headers,
                "html": p.raw_html,
            })

        robots_dict = self.robots_auditor.to_dict() if self.robots_auditor else {"status": 404, "text": None}
        sitemaps_list = self.robots_auditor.sitemaps if self.robots_auditor else []
        return {
            "site": self.site_url,
            "base_url": self.site_url,
            "crawled_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "pages": pages_data,
            "robots": robots_dict,
            "sitemaps": sitemaps_list,
            "infrastructure": {
                "homepage_reachable": len(self.pages) > 0,
                "sitemaps_discovered": sitemaps_list,
                "sitemaps_processed": len(sitemaps_list),
                "urls_extracted": self.frontier.total_seen(),
                "same_origin_urls": len(self.pages),
                "robots": robots_dict,
                "llms_txt": {
                    "status": 200 if self.llms_txt_content else 404,
                    "present": bool(self.llms_txt_content),
                    "snippet": self.llms_txt_content[:400] if self.llms_txt_content else None,
                },
                "llms_full_txt": {
                    "status": 200 if self.llms_full_txt_content else 404,
                    "present": bool(self.llms_full_txt_content),
                    "snippet": self.llms_full_txt_content[:400] if self.llms_full_txt_content else None,
                },
                "pricing_manifest": {
                    "status": self.pricing_manifest_status,
                    "present": bool(self.pricing_manifest_content),
                    "snippet": self.pricing_manifest_content[:400] if self.pricing_manifest_content else None,
                },
                "ai_plugin": {
                    "status": self.ai_plugin_status,
                    "present": bool(self.ai_plugin_content),
                    "snippet": self.ai_plugin_content[:400] if self.ai_plugin_content else None,
                },
                "security_txt": {
                    "status": self.security_txt_status,
                    "present": bool(self.security_txt_content),
                    "snippet": self.security_txt_content[:400] if self.security_txt_content else None,
                },
                "nav_fragment": {
                    "status": 200 if self.nav_fragment_content else 404,
                    "url": self.nav_fragment_url,
                    "present": bool(self.nav_fragment_content),
                    "links": self.nav_fragment_links,
                    "snippet": self.nav_fragment_content[:400] if self.nav_fragment_content else None,
                },
            },
            "stats": self.budget.get_stats(),
        }


# ==============================================================================
# SECTION 14: STANDALONE CLI RUNNER
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-Dependency Audit Web Engine CLI")
    parser.add_argument("--site", required=True, help="Target website URL to audit")
    parser.add_argument("--output", default="-", help="Output file path (default: stdout)")
    parser.add_argument("--max-pages", type=int, default=25, help="Maximum pages ceiling")
    parser.add_argument("--timeout", type=float, default=120.0, help="Audit timeout in seconds")
    parser.add_argument(
        "--format",
        choices=["inventory", "evidence", "both"],
        default="both",
        help="Output payload format",
    )
    parser.add_argument(
        "--allow-private-ips",
        action="store_true",
        help="Allow private IP addresses (for local test fixtures only)",
    )

    args = parser.parse_args()

    engine = WebAuditEngine(
        time_limit_sec=args.timeout,
        max_pages=args.max_pages,
        allow_private_ips=args.allow_private_ips,
    )

    try:
        evidence = engine.crawl(args.site)
    except Exception as e:
        sys.stderr.write(f"Crawl execution failed: {e}\n")
        sys.exit(1)

    if args.format == "inventory":
        result_payload: Dict[str, Any] = engine.to_inventory_dict()
    elif args.format == "evidence":
        result_payload = evidence.to_dict()
    else:
        result_payload = {
            "inventory": engine.to_inventory_dict(),
            "evidence": evidence.to_dict(),
        }

    output_json = json.dumps(result_payload, indent=2)

    if args.output == "-":
        sys.stdout.write(output_json + "\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
        sys.stderr.write(f"Successfully audited {args.site} ({len(engine.pages)} pages). Saved to {args.output}\n")


if __name__ == "__main__":
    main()
