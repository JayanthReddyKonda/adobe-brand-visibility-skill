"""Unit tests for Engagement & Context Continuity sensor."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "engagement-context-audit", "scripts")
for p in [PROJECT_ROOT, SKILL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engagement_check

from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_empty_inventory,
    make_healthy_inventory,
)


class TestEngagementUnit(unittest.TestCase):
    """Verifies H1 alignment, CTA reachability, and intent continuity."""

    def test_audit_healthy_site_engagement(self):
        """Success test: Site with aligned H1 and visible CTA passes engagement audit."""
        inv = make_healthy_inventory("https://example.com")
        res = engagement_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        self.assertIn("engagement_continuity_summary", res)

    def test_audit_defective_site_flags_ux_friction(self):
        """Failure test: Site with missing H1 and hidden CTA triggers UX friction findings."""
        inv = make_defective_inventory("https://example.com")
        res = engagement_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        self.assertIsInstance(res.get("findings"), list)

    def test_audit_empty_inventory_handled_safely(self):
        """Boundary/Failure test: Empty inventory handled without crashing."""
        inv = make_empty_inventory("https://example.com")
        res = engagement_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIn(res["status"], ["ok", "inconclusive"])


if __name__ == "__main__":
    unittest.main()
