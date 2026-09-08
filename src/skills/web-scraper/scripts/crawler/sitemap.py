"""XML Sitemap discoverer and parser for declared discovery paths.

Supports standard sitemaps (<urlset>), sitemap indices (<sitemapindex>),
namespace stripping, XML parsing with resilient regex fallback, and recursive traversal.
Pure Python standard library (xml.etree.ElementTree, re).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


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

    # XML namespace cleanup pattern
    _NS_REGEX = re.compile(r"\{[^\}]+\}")
    _URL_LOC_REGEX = re.compile(r"<loc>\s*(https?://[^\s<]+)", re.IGNORECASE)

    @classmethod
    def parse_sitemap(cls, content: str) -> Tuple[List[SitemapUrl], List[str]]:
        """Parses sitemap content and returns (urls, child_sitemap_urls)."""
        urls: List[SitemapUrl] = []
        child_sitemaps: List[str] = []

        if not content or not content.strip():
            return urls, child_sitemaps

        cleaned_content = content.strip()

        # Attempt structured XML parse first
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
                # Handle non-standard roots containing <loc> or <url>
                for elem in root.iter():
                    if cls._strip_ns(elem.tag).lower() == "loc" and elem.text:
                        loc_text = elem.text.strip()
                        if loc_text.startswith("http://") or loc_text.startswith("https://"):
                            urls.append(SitemapUrl(loc=loc_text))

            if not urls and not child_sitemaps:
                return cls._fallback_regex_parse(cleaned_content)

            return urls, child_sitemaps

        except ET.ParseError:
            # Fallback to regex extraction for malformed XML
            return cls._fallback_regex_parse(cleaned_content)

    @classmethod
    def _strip_ns(cls, tag: str) -> str:
        return cls._NS_REGEX.sub("", tag)

    @classmethod
    def _fallback_regex_parse(cls, content: str) -> Tuple[List[SitemapUrl], List[str]]:
        urls: List[SitemapUrl] = []
        child_sitemaps: List[str] = []

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
        """Traverse sitemap hierarchy starting from seed URLs."""
        from collections import deque

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
