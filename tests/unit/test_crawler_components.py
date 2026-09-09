"""Unit tests for crawler streaming parser, metadata, classification, and evidence extraction."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
if SCRAPER_DIR not in sys.path:
    sys.path.insert(0, SCRAPER_DIR)

from crawler.classify import PageClassifier
from crawler.evidence import EvidenceExtractor
from crawler.links import LinkProcessor
from crawler.metadata import MetadataProcessor
from crawler.parser import StreamingHTMLParser

from tests.fixtures.html_fixtures import (
    CLEAN_ENTERPRISE_HTML,
    CSR_EMPTY_SHELL_HTML,
    MALFORMED_HTML,
)


class TestCrawlerComponents(unittest.TestCase):
    """Verifies content extraction, streaming parsing, and page classification."""

    def test_streaming_parser_clean_html(self):
        """Success test: Streaming HTML parser extracts title, canonical, and headings."""
        parser = StreamingHTMLParser()
        parser.feed(CLEAN_ENTERPRISE_HTML)

        self.assertIn("Enterprise AI Cloud", parser.title)
        self.assertEqual(parser.canonical, "https://example.com/")
        self.assertTrue(len(parser.headings) >= 1)
        self.assertEqual(parser.headings[0].text, "Enterprise AI Cloud Infrastructure")
        self.assertIn("main", parser.semantic_landmarks)
        self.assertTrue(len(parser.tables) >= 1)
        self.assertEqual(parser.tables[0].headers, ["Metric", "Baseline", "Enterprise Cloud"])

    def test_streaming_parser_empty_shell(self):
        """Failure/Boundary test: Empty CSR shell yields no headings or tables."""
        parser = StreamingHTMLParser()
        parser.feed(CSR_EMPTY_SHELL_HTML)

        self.assertEqual(len(parser.headings), 0)
        self.assertEqual(len(parser.tables), 0)

    def test_streaming_parser_malformed_html(self):
        """Boundary test: Malformed HTML parses safely without unhandled exception."""
        parser = StreamingHTMLParser()
        parser.feed(MALFORMED_HTML)
        self.assertIn("Malformed", parser.title)

    def test_streaming_parser_cta_extraction(self):
        """Success test: Extracts interactive buttons, links, and classifies commercial intent."""
        html = """
        <html><body>
            <button type="button">Start Free Trial</button>
            <a href="/pricing" class="btn btn-primary">View Pricing Plans</a>
            <div role="button">Contact Sales</div>
            <a href="/about" class="action-link">Learn More</a>
            <a href="/faq">Regular Link</a>
        </body></html>
        """
        parser = StreamingHTMLParser()
        parser.feed(html)
        self.assertEqual(len(parser.ctas), 4)
        commercial_ctas = [c for c in parser.ctas if c.is_commercial_cta]
        self.assertEqual(len(commercial_ctas), 3)
        self.assertTrue(any("Trial" in c.text for c in commercial_ctas))
        self.assertTrue(any("Pricing" in c.text for c in commercial_ctas))
        self.assertTrue(any("Sales" in c.text for c in commercial_ctas))

    def test_streaming_parser_hreflang_extraction(self):
        """Success test: Extracts hreflang alternate links and feeds."""
        html = """
        <html><head>
            <link rel="alternate" hreflang="en-us" href="https://example.com/en-us/" />
            <link rel="alternate" hreflang="de-de" href="https://example.com/de-de/" />
            <link rel="alternate" type="application/rss+xml" href="https://example.com/feed.xml" />
        </head><body>Content</body></html>
        """
        parser = StreamingHTMLParser()
        parser.feed(html)
        self.assertEqual(len(parser.hreflangs), 2)
        self.assertEqual(parser.hreflangs[0].lang, "en-us")
        self.assertEqual(parser.hreflangs[0].href, "https://example.com/en-us/")
        self.assertEqual(len(parser.feed_links), 1)
        self.assertEqual(parser.feed_links[0], "https://example.com/feed.xml")

    def test_streaming_parser_http_headers(self):
        """Success test: Parses X-Robots-Tag, canonical Link header, and Last-Modified."""
        headers = {
            "X-Robots-Tag": "noindex, nofollow",
            "Link": '<https://example.com/canonical-page>; rel="canonical"',
            "Last-Modified": "Wed, 21 Oct 2025 07:28:00 GMT",
        }
        parser = StreamingHTMLParser()
        directives = parser.parse_http_headers(headers)
        self.assertIn("noindex", directives)
        self.assertIn("nofollow", directives)
        self.assertEqual(parser.canonical, "https://example.com/canonical-page")
        self.assertEqual(parser.dates["modified"], "Wed, 21 Oct 2025 07:28:00 GMT")

    def test_extract_contact_and_social_info(self):
        """Success test: Extracts emails, phones, and social authority links."""
        links = [
            "https://www.linkedin.com/company/acme-corp",
            "https://x.com/acmecorp",
            "https://github.com/acme-org",
            "https://example.com/internal-page",
            "mailto:press@acme.com",
            "tel:+1-800-555-0199",
        ]
        text = "Contact support at support@acme.com or call +1 (555) 234-5678."
        contact_info, social_links = EvidenceExtractor.extract_contact_and_social_info(text, links)

        self.assertIn("support@acme.com", contact_info["emails"])
        self.assertIn("+1 (555) 234-5678", contact_info["phones"])
        self.assertEqual(len(social_links), 3)
        self.assertIn("https://www.linkedin.com/company/acme-corp", social_links)
        self.assertIn("https://x.com/acmecorp", social_links)
        self.assertIn("https://github.com/acme-org", social_links)

    def test_page_classifier(self):
        """Success test: Correctly classifies homepage, pricing, and general routes."""
        classifier = PageClassifier()
        self.assertEqual(classifier.classify_route("https://example.com/"), "homepage")
        self.assertEqual(classifier.classify_route("https://example.com/pricing"), "pricing")
        self.assertEqual(classifier.classify_route("https://example.com/products/cluster"), "product")

    def test_link_processor_normalization(self):
        """Success test: Normalizes URLs, strips fragments, and filters non-HTTP schemes."""
        self.assertEqual(
            LinkProcessor.normalize_url("https://example.com/pricing#plans"),
            "https://example.com/pricing",
        )
        self.assertIsNone(LinkProcessor.normalize_url("mailto:support@example.com"))
        self.assertIsNone(LinkProcessor.normalize_url("javascript:void(0)"))

    def test_metadata_processor_robots_directives(self):
        """Success test: Extracts robots meta tags and identifies noindex."""
        meta_tags = [{"name": "robots", "content": "noindex, nofollow"}]
        metadata, obs = MetadataProcessor.process_metadata(meta_tags, "https://example.com/staging")
        self.assertIn("noindex", metadata["robots_directives"])
        self.assertTrue(any(o.value == "noindex_detected" for o in obs))


if __name__ == "__main__":
    unittest.main()
