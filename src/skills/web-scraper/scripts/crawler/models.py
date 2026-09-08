"""Data models and acquisition contracts for the Zero-Dependency Audit Web Engine.

Synthesizes contracts from Crawlee (Request/Resource), Scrapy (Item pipeline),
Crawl4AI (Token-aware Markdown, Structured Facts), and Trafilatura (Clean text, SNR).
Pure Python standard library (no pydantic, no external packages).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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

    def to_dict(self, include_raw_html: bool = False) -> Dict[str, Any]:
        """Convert page model to dictionary for JSON serialization."""
        data = {
            "url": self.url,
            "final_url": self.final_url,
            "status": self.status,
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "canonical": self.canonical,
            "canonicals": self.canonicals,
            "robots_meta": self.robots_meta,
            "language": self.language,
            "headings": [h.to_dict() for h in self.headings],
            "links": [link.to_dict() for link in self.links],
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
