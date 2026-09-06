"""Unit tests for Generative Engine Optimization (GEO) Citability sensor."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "geo-content-audit", "scripts")
for p in [PROJECT_ROOT, SKILL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import geo_content_check

from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_empty_inventory,
    make_healthy_inventory,
)


class TestGeoContentUnit(unittest.TestCase):
    """Verifies GEO citability vectors, BLUF placement, passage entropy, and hedge rate calculations."""

    def test_high_entropy_factual_text(self):
        """Success test: Diverse, technical vocabulary yields high token entropy."""
        text = (
            "Enterprise database latency dropped to 42 milliseconds because the distributed "
            "Raft consensus protocol batches IOPS transactions efficiently across 16 geo-replicated shards."
        )
        entropy = geo_content_check.compute_passage_entropy(text)
        self.assertGreater(entropy, 3.8)

    def test_low_entropy_promotional_repetition(self):
        """Failure test: Repetitive buzzwords yield lower token entropy."""
        text = (
            "Delve into our game-changer solution. This game-changer solution is a testament to our "
            "game-changer solution that helps you delve into more game-changer solutions."
        )
        entropy = geo_content_check.compute_passage_entropy(text)
        self.assertLess(entropy, 4.0)

    def test_compression_ratio_detection(self):
        """Test: Highly repetitive text is flagged via compression ratio."""
        repetitive = "testament " * 100
        ratio = geo_content_check.compute_compression_ratio(repetitive)
        self.assertLess(ratio, 0.20)

    def test_audit_healthy_site_citability(self):
        """Success test: Page with statistical evidence and causal conjunctions achieves good GEO score."""
        inv = make_healthy_inventory("https://example.com")
        res = geo_content_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        self.assertTrue("geo_citability_summary" in res or "citability_scores" in res)
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertNotIn("EXCESSIVE_HEDGE_LANGUAGE", cause_ids)

    def test_audit_hedgy_site_flags_excessive_hedges(self):
        """Failure test: Speculative/hedgy content triggers EXCESSIVE_HEDGE_LANGUAGE finding."""
        inv = make_defective_inventory("https://example.com")
        res = geo_content_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertIn("EXCESSIVE_HEDGE_LANGUAGE", cause_ids)

    def test_audit_empty_inventory_handled_safely(self):
        """Boundary/Failure test: Empty inventory handled without ZeroDivisionError."""
        inv = make_empty_inventory("https://example.com")
        res = geo_content_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIn(res["status"], ["ok", "inconclusive"])


if __name__ == "__main__":
    unittest.main()
