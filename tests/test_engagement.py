import os
import sys
import unittest

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/skills/engagement-context-audit/scripts"))
sys.path.insert(0, script_dir)

import engagement_check


class TestEngagement(unittest.TestCase):
    def test_pricing_fact_matcher_handles_boundaries(self):
        engine = engagement_check.SemanticIntentEngine(
            os.path.join(script_dir, "../references")
        )
        required = ["tier_names", "billing_interval", "tier_prices", "signup_or_trial_cta"]
        self.assertEqual(engine.check_facts_in_text("Pro plan: $49/mo. Start today", required), [])

    def test_no_h1(self):
        html = "<html><body><p>No H1 here</p></body></html>"
        findings, recs, _metrics = engagement_check.audit_page_engagement(html, "http://example.com/", "other")

        # Verify no finding is created solely because of no H1
        for f in findings:
            if f["title"] == "Missing primary heading (H1)":
                self.fail("No H1 alone generated a finding instead of a recommendation.")

        # Verify recommendation is created
        has_rec = any("Ensure every page provides a clear <h1>" in r["summary"] for r in recs)
        self.assertTrue(has_rec, "Missing H1 did not generate a recommendation.")


if __name__ == "__main__":
    unittest.main()
