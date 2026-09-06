"""Integration tests for web-scraper crawler pipeline and inventory output."""

import json
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
if SCRAPER_DIR not in sys.path:
    sys.path.insert(0, SCRAPER_DIR)

from crawler.engine import WebAuditEngine

from tests.helpers.cli_runner import run_skill_script


class TestCrawlerPipeline(unittest.TestCase):
    """Verifies end-to-end crawler acquisition pipeline."""

    def test_engine_initialization_and_to_inventory_dict(self):
        """Success test: Engine initializes and produces compliant inventory dictionary."""
        engine = WebAuditEngine(time_limit_sec=5.0, max_pages=2)
        inv = engine.to_inventory_dict()
        self.assertIn("site", inv)
        self.assertIn("pages", inv)
        self.assertIn("robots", inv)
        self.assertIn("sitemaps", inv)
        self.assertIn("infrastructure", inv)
        self.assertIsInstance(inv["pages"], list)

    def test_run_scraper_cli_output(self):
        """Integration test: CLI invocation produces structured inventory."""
        temp_inv = os.path.join(tempfile.gettempdir(), "test_pipeline_run.json")
        try:
            res = run_skill_script(
                "web-scraper",
                "run_scraper.py",
                [
                    "--site",
                    "https://example.com",
                    "--output",
                    temp_inv,
                    "--max-pages",
                    "1",
                    "--timeout",
                    "5",
                ],
            )
            # Should exit cleanly (exit 0)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(temp_inv))
            with open(temp_inv, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("site", data)
            self.assertIn("pages", data)
        finally:
            if os.path.exists(temp_inv):
                os.remove(temp_inv)


if __name__ == "__main__":
    unittest.main()
