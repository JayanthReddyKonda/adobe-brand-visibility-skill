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


if __name__ == "__main__":
    unittest.main()
