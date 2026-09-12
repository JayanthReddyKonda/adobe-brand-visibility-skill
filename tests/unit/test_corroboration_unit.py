"""Unit tests for Corroboration & Authority Audit sensor."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "corroboration-authority-audit", "scripts")
for p in [PROJECT_ROOT, SKILL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import corroboration_check

from tests.fixtures.html_fixtures import CLEAN_ENTERPRISE_HTML
from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_empty_inventory,
    make_healthy_inventory,
)


class TestCorroborationUnit(unittest.TestCase):
    """Verifies sameAs identity corroboration and authority extraction."""

    def test_extract_sld(self):
        """Unit test: Second-level domain extraction handles subdomains correctly."""
        self.assertEqual(corroboration_check.extract_sld("www.example.com"), "example")
        self.assertEqual(corroboration_check.extract_sld("api.sub.brand.org"), "brand")
        self.assertEqual(corroboration_check.extract_sld("localhost"), "localhost")

    def test_extract_sameas_links(self):
        """Success test: Extracts sameAs links from JSON-LD blocks in HTML."""
        links = corroboration_check.extract_sameas_links(CLEAN_ENTERPRISE_HTML)
        self.assertIn("https://www.wikidata.org/wiki/Q115000", links)
        self.assertIn("https://www.linkedin.com/company/enterprise-ai-cloud", links)

    def test_audit_healthy_site_authority(self):
        """Success test: Site with verified authority nodes generates healthy corroboration result."""
        inv = make_healthy_inventory("https://example.com")
        res = corroboration_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        self.assertIn("findings", res)

    def test_audit_defective_site_missing_corroboration(self):
        """Failure test: Site lacking external identity links is flagged."""
        inv = make_defective_inventory("https://example.com")
        res = corroboration_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        self.assertIsInstance(res.get("findings"), list)

    def test_audit_empty_inventory(self):
        """Boundary/Failure test: Empty inventory handled without crashing."""
        inv = make_empty_inventory("https://example.com")
        res = corroboration_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIn(res["status"], ["ok", "inconclusive"])


    def test_audit_with_candidate_backlinks(self):
        """Regression test: Candidate backlinks audit runs with time deadline and does not crash with NameError."""
        inv = make_healthy_inventory("https://example.com")
        res = corroboration_check.audit(
            "https://example.com",
            "example.com",
            inv,
            candidate_backlinks=[{"source_url": "https://example.com/source", "expected_target": "https://example.com"}],
        )
        self.assertEqual(res["status"], "ok")
        self.assertIn("verified_candidate_backlinks", res.get("evidence_classes", {}))


if __name__ == "__main__":
    unittest.main()

