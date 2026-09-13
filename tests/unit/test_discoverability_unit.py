"""Unit tests for Discoverability & Retrieval Audit sensor."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "discoverability-audit", "scripts")
for p in [PROJECT_ROOT, SKILL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import discoverability_check

from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_empty_inventory,
    make_healthy_inventory,
)


class TestDiscoverabilityUnit(unittest.TestCase):
    """Verifies discoverability sensor audit logic."""

    def test_hreflang_validation(self):
        """Unit test: Valid BCP 47 hreflang codes pass; invalid formats fail."""
        self.assertTrue(discoverability_check.is_valid_hreflang("en-US"))
        self.assertTrue(discoverability_check.is_valid_hreflang("fr-CA"))
        self.assertTrue(discoverability_check.is_valid_hreflang("de"))
        self.assertFalse(discoverability_check.is_valid_hreflang("en_US"))  # underscore invalid
        self.assertFalse(discoverability_check.is_valid_hreflang("en-uk"))  # lowercase region invalid

    def test_audit_healthy_site(self):
        """Success test: Healthy site produces status 'ok' and 0 critical defects."""
        inv = make_healthy_inventory("https://example.com")
        res = discoverability_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        findings = res.get("findings", [])
        severities = [f.get("severity") for f in findings if isinstance(f, dict)]
        self.assertNotIn("critical", severities)

    def test_audit_defective_site_flags_hard_failures(self):
        """Failure test: Defective inventory triggers AI_RETRIEVAL_BLOCKED and NOINDEX_EXCLUSION."""
        inv = make_defective_inventory("https://example.com")
        res = discoverability_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertIn("AI_RETRIEVAL_BLOCKED", cause_ids)
        self.assertIn("NOINDEX_EXCLUSION", cause_ids)

    def test_audit_empty_inventory_resilience(self):
        """Boundary/Failure test: Empty inventory handles gracefully without traceback."""
        inv = make_empty_inventory("https://example.com")
        res = discoverability_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIsInstance(res.get("findings"), list)

    def test_broken_primary_nav_route(self):
        """Failure test: Navigation fragment referencing a 404 endpoint emits B4_BROKEN_PRIMARY_NAV_ROUTE."""
        inv = {
            "site": "https://example.com",
            "infrastructure": {
                "nav_fragment": {
                    "status": 200,
                    "url": "https://example.com/nav.plain.html",
                    "links": ["https://example.com/products", "https://example.com/dead-route"],
                }
            },
            "pages": [
                {"url": "https://example.com/", "status": 200, "html": "<html><body>Home</body></html>"},
                {"url": "https://example.com/products", "status": 200, "html": "<html><body>Products</body></html>"},
                {"url": "https://example.com/dead-route", "status": 404, "html": "<html><body>Not Found</body></html>"},
            ],
        }
        res = discoverability_check.audit("https://example.com", "example.com", inv)
        findings = res.get("findings", [])
        nav_broken = [f for f in findings if f.get("id") == "B4_BROKEN_PRIMARY_NAV_ROUTE"]
        self.assertTrue(len(nav_broken) > 0)
        self.assertEqual(nav_broken[0]["cause_id"], "BROKEN_LINK")
        self.assertEqual(nav_broken[0]["severity"], "high")

    def test_form_gated_entity_discovery(self):
        """Failure test: Store locator gating store locations behind postal code input emits B5_FORM_GATED_ENTITY_DISCOVERY."""
        inv = {
            "site": "https://example.com",
            "pages": [
                {
                    "url": "https://example.com/locations",
                    "status": 200,
                    "html": '<div class="store-locator"><h2>Find A Location</h2><form><label>Post Code</label><input type="text"><button>Search</button></form></div>',
                    "clean_text": "Find A Location Post Code Search",
                    "links": [],
                    "schemas": [],
                }
            ],
        }
        res = discoverability_check.audit("https://example.com", "example.com", inv)
        findings = res.get("findings", [])
        form_gated = [f for f in findings if f.get("id") == "B5_FORM_GATED_ENTITY_DISCOVERY"]
        self.assertTrue(len(form_gated) > 0)
        self.assertEqual(form_gated[0]["cause_id"], "FORM_GATED_DISCOVERY_TRAP")
        self.assertEqual(form_gated[0]["severity"], "medium")


if __name__ == "__main__":
    unittest.main()
