"""Unit tests for the web-scraper skill and its CLI entrypoint (run_scraper.py)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
SCRAPER_SCRIPTS_DIR = os.path.join(SRC_DIR, "skills", "web-scraper", "scripts")

for p in [SRC_DIR, SCRAPER_SCRIPTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import run_scraper
from crawler.models import PageModel


class TestWebScraperSkill(unittest.TestCase):
    """Test suite for the web-scraper skill interface and CLI."""

    def test_evals_json_valid(self):
        evals_path = os.path.join(SRC_DIR, "skills", "web-scraper", "evals", "evals.json")
        self.assertTrue(os.path.exists(evals_path), "evals.json must exist")
        with open(evals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("skill_name"), "web-scraper")
        self.assertIn("evals", data)
        self.assertTrue(len(data["evals"]) >= 3)

    def test_skill_md_structure(self):
        skill_md_path = os.path.join(SRC_DIR, "skills", "web-scraper", "SKILL.md")
        self.assertTrue(os.path.exists(skill_md_path), "SKILL.md must exist")
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(content.startswith("---"), "SKILL.md must have YAML frontmatter")
        self.assertIn("name: web-scraper", content)
        self.assertIn("# Web Scraper Skill", content)
        self.assertIn("## When to Use", content)
        self.assertIn("## Inputs", content)
        self.assertIn("## Procedure", content)
        self.assertIn("## Output Contract", content)

    def test_format_markdown_summary(self):
        mock_inv = {
            "site": "https://testbrand.com",
            "crawled_at": "2026-09-06T12:00:00Z",
            "robots": {
                "status": 200,
                "matrix": {
                    "OAI-SearchBot": True,
                    "PerplexityBot": False,
                },
            },
            "sitemaps": ["https://testbrand.com/sitemap.xml"],
            "stats": {"total_bytes": 10240, "elapsed_seconds": 0.85},
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "page_type": "homepage",
                    "status": 200,
                    "snr_ratio": 0.35,
                    "word_count": 450,
                    "jsonld": [{"@type": "Organization", "name": "TestBrand"}],
                }
            ],
        }
        md = run_scraper.format_markdown_summary(mock_inv)
        self.assertIn("# Web Scraping Inventory: https://testbrand.com", md)
        self.assertIn("OAI-SearchBot", md)
        self.assertIn("PerplexityBot", md)
        self.assertIn("https://testbrand.com/", md)
        self.assertIn("450", md)

    @patch("run_scraper.WebAuditEngine")
    def test_run_scraper_cli_execution(self, mock_engine_cls):
        mock_engine = MagicMock()
        mock_engine.pages = {
            "https://testbrand.com/": PageModel(
                url="https://testbrand.com/",
                final_url="https://testbrand.com/",
                status=200,
                word_count=120,
            )
        }
        mock_engine.to_inventory_dict.return_value = {
            "site": "https://testbrand.com",
            "crawled_at": "2026-09-06T12:00:00Z",
            "robots": {"status": 200, "matrix": {}},
            "sitemaps": [],
            "pages": [{"url": "https://testbrand.com/", "page_type": "homepage", "status": 200}],
            "infrastructure": {},
            "stats": {"pages_crawled": 1, "total_bytes": 500},
        }
        mock_engine_cls.return_value = mock_engine

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            test_args = [
                "run_scraper.py",
                "--site",
                "https://testbrand.com",
                "--output",
                tmp_path,
                "--max-pages",
                "5",
                "--timeout",
                "10.0",
                "--format",
                "json",
            ]
            with patch.object(sys, "argv", test_args):
                exit_code = run_scraper.main()
                self.assertEqual(exit_code, 0)

            mock_engine.crawl.assert_called_once_with("https://testbrand.com")
            self.assertTrue(os.path.exists(tmp_path))
            with open(tmp_path, "r", encoding="utf-8") as f:
                saved_inv = json.load(f)
            self.assertEqual(saved_inv.get("site"), "https://testbrand.com")
            self.assertEqual(len(saved_inv.get("pages", [])), 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
