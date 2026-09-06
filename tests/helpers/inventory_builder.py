"""Inventory builder for creating synthetic test site inventories."""

import json
from typing import Optional

from tests.fixtures.html_fixtures import (
    CLEAN_ENTERPRISE_HTML,
    CONFLICTING_PRICING_HTML,
    CSR_EMPTY_SHELL_HTML,
    HEDGY_TEXT_HTML,
    HIDDEN_CTA_HTML,
    MISSING_H1_HTML,
    NOINDEX_HTML,
    PRICING_PAGE_HTML,
)
from tests.fixtures.robots_fixtures import (
    BLOCKING_RETRIEVAL_BOTS_ROBOTS_TXT,
    PERMISSIVE_ROBOTS_TXT,
)


class InventoryBuilder:
    """Fluent builder for constructing site inventory fixtures."""

    def __init__(self, site: str = "https://example.com"):
        self.site = site
        self.pages = []
        self.robots_txt = PERMISSIVE_ROBOTS_TXT
        self.sitemaps = [f"{site}/sitemap.xml"]
        self.infrastructure = {"server": "cloudflare", "http_version": "HTTP/2"}

    def add_page(
        self,
        url: str,
        html: str,
        status: int = 200,
        content_type: str = "text/html",
        page_type: str = "article",
        jsonld: Optional[list] = None,
        snr_ratio: float = 0.25,
        word_count: int = 350,
    ):
        page = {
            "url": url,
            "status": status,
            "content_type": content_type,
            "page_type": page_type,
            "html": html,
            "jsonld": jsonld or [],
            "snr_ratio": snr_ratio,
            "word_count": word_count,
        }
        self.pages.append(page)
        return self

    def set_robots_txt(self, robots_txt: str):
        self.robots_txt = robots_txt
        return self

    def set_sitemaps(self, sitemaps: list):
        self.sitemaps = sitemaps
        return self

    def build(self) -> dict:
        return {
            "site": self.site,
            "pages": list(self.pages),
            "robots_txt": self.robots_txt,
            "sitemaps": list(self.sitemaps),
            "infrastructure": dict(self.infrastructure),
        }

    def to_json(self) -> str:
        return json.dumps(self.build(), indent=2)


def make_healthy_inventory(site: str = "https://example.com") -> dict:
    """Builds a comprehensive, compliant site inventory with 0 defects."""
    return (
        InventoryBuilder(site)
        .set_robots_txt(PERMISSIVE_ROBOTS_TXT)
        .add_page(
            url=f"{site}/",
            html=CLEAN_ENTERPRISE_HTML,
            page_type="homepage",
            snr_ratio=0.32,
            word_count=450,
        )
        .add_page(
            url=f"{site}/pricing",
            html=PRICING_PAGE_HTML,
            page_type="pricing",
            snr_ratio=0.28,
            word_count=320,
        )
        .build()
    )


def make_defective_inventory(site: str = "https://example.com") -> dict:
    """Builds a site inventory triggering all canonical hard failure modes (HF-01 to HF-08)."""
    return (
        InventoryBuilder(site)
        .set_robots_txt(BLOCKING_RETRIEVAL_BOTS_ROBOTS_TXT)  # HF-01
        .add_page(
            url=f"{site}/",
            html=NOINDEX_HTML,  # HF-02
            page_type="homepage",
            snr_ratio=0.08,
            word_count=25,
        )
        .add_page(
            url=f"{site}/app",
            html=CSR_EMPTY_SHELL_HTML,  # HF-03
            page_type="application",
            snr_ratio=0.01,
            word_count=0,
        )
        .add_page(
            url=f"{site}/pricing",
            html=PRICING_PAGE_HTML,
            page_type="pricing",
            snr_ratio=0.28,
            word_count=320,
        )
        .add_page(
            url=f"{site}/pricing-conflicted",
            html=CONFLICTING_PRICING_HTML,  # HF-06
            page_type="pricing",
            snr_ratio=0.20,
            word_count=200,
        )
        .add_page(
            url=f"{site}/hedgy",
            html=HEDGY_TEXT_HTML,  # HF-08
            page_type="article",
            snr_ratio=0.15,
            word_count=180,
        )
        .add_page(
            url=f"{site}/missing-h1",
            html=MISSING_H1_HTML,
            page_type="product",
            snr_ratio=0.14,
            word_count=120,
        )
        .add_page(
            url=f"{site}/hidden-cta",
            html=HIDDEN_CTA_HTML,
            page_type="article",
            snr_ratio=0.18,
            word_count=220,
        )
        .build()
    )


def make_empty_inventory(site: str = "https://example.com") -> dict:
    """Builds a minimal inventory with 0 pages (e.g. crawl failed or down)."""
    return {
        "site": site,
        "pages": [],
        "robots_txt": "",
        "sitemaps": [],
        "infrastructure": {},
    }
