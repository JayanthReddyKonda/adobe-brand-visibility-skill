"""Unit tests for RFC 9309 robots.txt evaluator and XML sitemap parser."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
if SCRAPER_DIR not in sys.path:
    sys.path.insert(0, SCRAPER_DIR)

from crawler.robots import (
    RobotsAuditor,
    RobotsOutcome,
)
from crawler.sitemap import SitemapParser

from tests.fixtures.robots_fixtures import (
    BLOCKING_RETRIEVAL_BOTS_ROBOTS_TXT,
    BLOCKING_TRAINING_ONLY_ROBOTS_TXT,
    PERMISSIVE_ROBOTS_TXT,
)
from tests.fixtures.sitemap_fixtures import (
    MALFORMED_SITEMAP_XML,
    VALID_SITEMAP_INDEX_XML,
    VALID_SITEMAP_XML,
)


class TestRobotsAndSitemaps(unittest.TestCase):
    """Verifies robots.txt RFC 9309 compliance and sitemap parsing."""

    def test_robots_permissive(self):
        """Success test: Permissive robots allows all bots."""
        auditor = RobotsAuditor(content=PERMISSIVE_ROBOTS_TXT, status_code=200)
        self.assertTrue(auditor.is_allowed("https://example.com/test", "OAI-SearchBot"))
        self.assertTrue(auditor.is_allowed("https://example.com/test", "GPTBot"))
        self.assertTrue(auditor.is_allowed("https://example.com/test", "*"))

    def test_robots_blocking_retrieval_bots(self):
        """Failure test: Specific disallow blocks AI SearchBots."""
        auditor = RobotsAuditor(content=BLOCKING_RETRIEVAL_BOTS_ROBOTS_TXT, status_code=200)
        self.assertFalse(auditor.is_allowed("https://example.com/", "OAI-SearchBot"))
        self.assertFalse(auditor.is_allowed("https://example.com/page", "Claude-SearchBot"))
        self.assertFalse(auditor.is_allowed("https://example.com/", "PerplexityBot"))
        # Wildcard user-agent is allowed
        self.assertTrue(auditor.is_allowed("https://example.com/", "Googlebot"))

    def test_robots_training_vs_retrieval(self):
        """Test distinction: Training bot blocked while retrieval bot allowed."""
        auditor = RobotsAuditor(content=BLOCKING_TRAINING_ONLY_ROBOTS_TXT, status_code=200)
        self.assertFalse(auditor.is_allowed("https://example.com/", "GPTBot"))
        self.assertTrue(auditor.is_allowed("https://example.com/", "OAI-SearchBot"))

    def test_robots_server_error_fail_closed(self):
        """Failure/Boundary test: HTTP 500 status code triggers fail-closed (all blocked)."""
        auditor = RobotsAuditor(content="", status_code=500, outcome=RobotsOutcome.SERVER_ERROR)
        self.assertFalse(auditor.is_allowed("https://example.com/any", "OAI-SearchBot"))
        self.assertFalse(auditor.is_allowed("https://example.com/any", "*"))

    def test_robots_not_found_fail_open(self):
        """Success/Boundary test: HTTP 404 status code triggers fail-open (all allowed)."""
        auditor = RobotsAuditor(content="", status_code=404, outcome=RobotsOutcome.NOT_FOUND)
        self.assertTrue(auditor.is_allowed("https://example.com/any", "OAI-SearchBot"))
        self.assertTrue(auditor.is_allowed("https://example.com/any", "*"))

    def test_sitemap_parse_valid_urlset(self):
        """Success test: Valid XML sitemap extracts all declared URLs."""
        urls, children = SitemapParser.parse_sitemap(VALID_SITEMAP_XML)
        self.assertEqual(len(urls), 2)
        locs = [u.loc for u in urls]
        self.assertIn("https://example.com/", locs)
        self.assertIn("https://example.com/pricing", locs)
        self.assertEqual(len(children), 0)

    def test_sitemap_index_parse(self):
        """Success test: Sitemap index extracts child sitemap URLs."""
        urls, children = SitemapParser.parse_sitemap(VALID_SITEMAP_INDEX_XML)
        self.assertEqual(len(urls), 0)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], "https://example.com/sitemap1.xml")

    def test_sitemap_malformed_fallback(self):
        """Boundary/Failure test: Malformed XML falls back to regex extraction cleanly."""
        urls, children = SitemapParser.parse_sitemap(MALFORMED_SITEMAP_XML)
        self.assertIsInstance(urls, list)
        self.assertGreaterEqual(len(urls), 1)
        self.assertEqual(urls[0].loc, "https://example.com/broken")

    def test_sitemap_empty_string(self):
        """Empty input test: Empty sitemap returns empty lists without error."""
        urls, children = SitemapParser.parse_sitemap("")
        self.assertEqual(urls, [])
        self.assertEqual(children, [])


if __name__ == "__main__":
    unittest.main()
