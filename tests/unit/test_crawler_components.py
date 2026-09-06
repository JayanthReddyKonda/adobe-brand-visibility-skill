"""Unit tests for crawler streaming parser, metadata, classification, and evidence extraction."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
if SCRAPER_DIR not in sys.path:
    sys.path.insert(0, SCRAPER_DIR)

from crawler.classify import PageClassifier
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
