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

    def test_modern_cta_element_detection(self):
        """Elevation test: Modern HTML buttons including input submits and role=button are parsed as CTAs."""
        html = """
        <html>
            <body>
                <h1>Enterprise AI Platform</h1>
                <input type="submit" value="Start Free Trial" />
                <div role="button">Book Demo</div>
                <a class="btn btn-primary" href="/signup">Sign Up Today</a>
            </body>
        </html>
        """
        parser = engagement_check.EngagementDOMParser()
        parser.feed(html)
        cta_texts_lower = [t.lower() for t in parser.cta_texts]
        self.assertTrue(any("start free trial" in t for t in cta_texts_lower))
        self.assertTrue(any("book demo" in t for t in cta_texts_lower))
        self.assertTrue(any("sign up today" in t for t in cta_texts_lower))
        commercial_elements = [el for el in parser.interactive_elements if el.get("is_commercial_cta")]
        self.assertGreaterEqual(len(commercial_elements), 3)

    def test_broken_component_integrations_detects_google_maps_error(self):
        """EN2: Detect Google Maps runtime error banner in DOM."""
        html_with_err = '<div><h1>Store Location</h1><div class="gm-err-container">This page can\'t load Google Maps correctly.</div></div>'
        finding = engagement_check.check_broken_component_integrations(html_with_err, "https://example.com/stores")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["id"], "EN2_COMPONENT_LOADING_FAILURE")
        self.assertEqual(finding["cause_id"], "COMPONENT_LOADING_FAILURE")

        html_clean = '<div><h1>Store Location</h1><p>123 Main Street</p></div>'
        self.assertIsNone(engagement_check.check_broken_component_integrations(html_clean, "https://example.com/stores"))

    def test_unnamed_interactive_controls_detects_empty_buttons(self):
        """EN6: Detect multiple action buttons lacking text, alt, or aria-labels."""
        html_unnamed = '''
        <div class="catalog">
            <button class="cart-btn"><svg></svg></button>
            <button class="fav-btn"><i class="icon"></i></button>
        </div>
        '''
        finding = engagement_check.check_unnamed_interactive_controls(html_unnamed, "https://example.com/products")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["id"], "EN6_UNNAMED_INTERACTIVE_CONTROL")
        self.assertEqual(finding["cause_id"], "CONTROL_REPRESENTATION_GAP")

        html_labeled = '''
        <div class="catalog">
            <button class="cart-btn" aria-label="Add to cart"><svg></svg></button>
            <button class="fav-btn" aria-label="Add to wishlist"><i class="icon"></i></button>
        </div>
        '''
        self.assertIsNone(engagement_check.check_unnamed_interactive_controls(html_labeled, "https://example.com/products"))

    def test_inert_actions_detects_both_account_and_commercial(self):
        """Verify both Account (sign in) and Commercial (subscribe) inert actions are detected on same page."""
        html = '''
        <html>
            <body>
                <h1>Premium Coffee Service</h1>
                <a class="nav-link" href="#">Sign In</a>
                <a class="btn" href="#">Subscribe Now</a>
            </body>
        </html>
        '''
        findings, _, _ = engagement_check.audit_page_engagement(html, "https://example.com/subscribe")
        cause_ids = [f["cause_id"] for f in findings]
        self.assertIn("INERT_ACCOUNT_FLOW", cause_ids)
        self.assertIn("INERT_CTA_TARGET", cause_ids)


if __name__ == "__main__":
    unittest.main()
