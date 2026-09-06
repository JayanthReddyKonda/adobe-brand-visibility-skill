"""Granular URL and content classifier for page type determination.

Classifies pages into architectural roles (homepage, product_detail, pricing, about,
contact, documentation, faq, article, category) with confidence estimates.
Pure Python standard library.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


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
        """Classifies page type and returns dict with 'value' and 'confidence' float."""
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
        """Classify a URL path into a simplified route category string."""
        res = cls.classify(url)
        val = res.get("value", "general")
        if val == "product_detail":
            return "product"
        return val
