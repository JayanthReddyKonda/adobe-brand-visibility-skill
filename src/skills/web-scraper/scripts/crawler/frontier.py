"""Priority-driven URL frontier with heuristic scoring and deduplication.

Prioritizes commercially critical routes (pricing, products, about, contact)
over deep archives, pagination, and blog listings.
Pure Python standard library (heapq, threading.Lock, urllib.parse).
"""

from __future__ import annotations

import heapq
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Set
from urllib.parse import urlparse


@dataclass(order=True)
class FrontierItem:
    """Prioritized queue item for the crawler frontier."""

    # heapq sorts by priority ascending; we invert priority so highest score pops first
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

    # Route weight lookup table based on semantic importance to brand audits
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
        "cart": 10.0,
        "checkout": 10.0,
        "login": 10.0,
        "signin": 10.0,
        "signup": 10.0,
        "register": 10.0,
        "auth": 10.0,
        "admin": 5.0,
    }

    def __init__(self, max_capacity: int = 2000) -> None:
        self.max_capacity = max_capacity
        self._heap: list[FrontierItem] = []
        self._enqueued: Set[str] = set()
        self._visited: Set[str] = set()
        self._lock = threading.Lock()

    def compute_priority(self, url: str, depth: int, is_sitemap_declared: bool = False) -> float:
        """Computes a numeric priority score for a given URL."""
        parsed = urlparse(url)
        path = (parsed.path or "/").lower().strip("/")

        # Base score
        base_score = 40.0

        if not path:
            base_score = self.ROUTE_WEIGHTS["/"]
        else:
            segments = path.split("/")
            first_seg = segments[0]
            if first_seg in self.ROUTE_WEIGHTS:
                base_score = self.ROUTE_WEIGHTS[first_seg]
            else:
                # Check for substring matches in segments
                for route_key, weight in self.ROUTE_WEIGHTS.items():
                    if route_key in path:
                        base_score = max(base_score, weight * 0.9)

        # Bonus for sitemap-declared URLs (explicit publisher endorsement)
        sitemap_bonus = 15.0 if is_sitemap_declared else 0.0

        # Depth penalty (prefer shallow pages closer to root)
        depth_penalty = depth * 15.0

        # Query penalty (prefer canonical clean URLs)
        query_penalty = 10.0 if parsed.query else 0.0

        return base_score + sitemap_bonus - depth_penalty - query_penalty

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

            priority = self.compute_priority(url, depth, is_sitemap_declared)
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
        """Marks a URL as visited."""
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
