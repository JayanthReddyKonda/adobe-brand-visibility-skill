"""Zero-Dependency Audit Web Engine for Brand AI-Readiness & Visibility.

Pure Python standard library web acquisition, streaming HTML parsing,
robots/sitemap discovery, Trafilatura boilerplate stripping, and agent query API.
"""

from .budget import Budget, BudgetExhaustedError
from .canonical import CanonicalValidator
from .classify import PageClassifier
from .engine import WebAuditEngine
from .evidence import EvidenceExtractor
from .fetch import SafeFetcher
from .frontier import Frontier, FrontierItem
from .jsonld import JsonLdExtractor
from .links import LinkProcessor
from .metadata import MetadataProcessor
from .models import (
    ClaimCandidate,
    EvidenceModel,
    FactCandidate,
    Heading,
    Link,
    Observation,
    PageModel,
    Resource,
    TableData,
)
from .policy import SecurityPolicy, SecurityValidationError
from .robots import RobotsAuditor, RobotsOutcome
from .sitemap import SitemapDiscovery, SitemapParser, SitemapUrl

__all__ = [
    "WebAuditEngine",
    "Budget",
    "BudgetExhaustedError",
    "SecurityPolicy",
    "SecurityValidationError",
    "SafeFetcher",
    "RobotsAuditor",
    "RobotsOutcome",
    "SitemapParser",
    "SitemapDiscovery",
    "SitemapUrl",
    "Frontier",
    "FrontierItem",
    "LinkProcessor",
    "JsonLdExtractor",
    "MetadataProcessor",
    "PageClassifier",
    "CanonicalValidator",
    "EvidenceExtractor",
    "Resource",
    "PageModel",
    "EvidenceModel",
    "FactCandidate",
    "ClaimCandidate",
    "Observation",
    "Heading",
    "Link",
    "TableData",
]
