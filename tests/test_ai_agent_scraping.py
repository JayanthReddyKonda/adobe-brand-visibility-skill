import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, "src/skills/audit-orchestrator/scripts")
sys.path.insert(0, "src/skills/discoverability-audit/scripts")

import acquire_inventory


class TestAIAgentScrapingOptimization(unittest.TestCase):
    def setUp(self):
        self.disc_script = "src/skills/discoverability-audit/scripts/discoverability_check.py"
        self.inv_script = "src/skills/audit-orchestrator/scripts/acquire_inventory.py"
        self.test_inv = os.path.join(tempfile.gettempdir(), "test_scrape_inv.json")

    def tearDown(self):
        if os.path.exists(self.test_inv):
            try:
                os.remove(self.test_inv)
            except OSError:
                pass

    def test_extract_clean_content_strips_boilerplate(self):
        """Verify HTML-to-clean-text extraction strips navigation chrome, headers, footers, and scripts."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title><style>.btn { color: red; }</style></head>
        <body>
            <header><nav><a href="/">Home</a><a href="/about">About</a></nav></header>
            <main>
                <h1>Autonomous AI Agent Architecture</h1>
                <p>Autonomous agents parse web documents using semantic markdown extraction.</p>
                <article>
                    <h2>Retrieval Pipeline</h2>
                    <p>Context windows require high signal-to-noise ratio to prevent token exhaustion.</p>
                </article>
            </main>
            <aside><h3>Sidebar Ads</h3><p>Buy our sponsored product!</p></aside>
            <footer><p>&copy; 2026 TestBrand Inc. All rights reserved.</p></footer>
            <script>console.log("tracking code");</script>
        </body>
        </html>
        """
        res = acquire_inventory.extract_clean_content(html)
        self.assertTrue(res["has_main"])
        self.assertTrue(res["has_article"])
        self.assertTrue(res["has_header"])
        self.assertTrue(res["has_nav"])
        self.assertTrue(res["has_footer"])

        # Main text should be present
        self.assertIn("Autonomous AI Agent Architecture", res["clean_text"])
        self.assertIn("Retrieval Pipeline", res["clean_text"])
        self.assertIn("Context windows require high signal-to-noise ratio", res["clean_text"])

        # Boilerplate in nav, aside, footer, script, style should be stripped
        self.assertNotIn("Sidebar Ads", res["clean_text"])
        self.assertNotIn("tracking code", res["clean_text"])
        self.assertNotIn(".btn { color: red; }", res["clean_text"])
        self.assertNotIn("All rights reserved", res["clean_text"])
        self.assertGreater(res["snr"], 0.05)
        self.assertGreater(res["clean_word_count"], 15)

    def test_llms_full_txt_recommendation_when_only_llmstxt_exists(self):
        """When /llms.txt exists but /llms-full.txt is missing, emit PROACTIVE.DISCOVERY.LLMS_FULL_TXT.001."""
        inv_data = {
            "site": "https://testbrand.com",
            "infrastructure": {
                "llms_txt": {"status": 200, "present": True, "snippet": "# TestBrand\n> Summary"},
                "llms_full_txt": {"status": 404, "present": False, "snippet": None},
                "robots": {"status": 200, "text": "User-agent: *\nAllow: /\n"},
            },
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><main><h1>TestBrand</h1><p>Main content here with enough words to satisfy threshold.</p></main></body></html>",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            ["python3", self.disc_script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        rec_ids = [r.get("id") for r in data.get("recommendations", [])]
        self.assertIn("PROACTIVE.DISCOVERY.LLMS_FULL_TXT.001", rec_ids)
        self.assertNotIn("PROACTIVE.DISCOVERY.LLMS_TXT.001", rec_ids)

        # Check ai_agent_scrapeability_summary
        self.assertIn("ai_agent_scrapeability_summary", data)
        summary = data["ai_agent_scrapeability_summary"]
        self.assertTrue(summary["llms_txt_present"])
        self.assertFalse(summary["llms_full_txt_present"])
        self.assertGreater(summary["overall_scrapeability_score"], 60)

    def test_semantic_landmarks_recommendation_when_lacking_main_and_article(self):
        """When a page uses pure generic <div> soup without <main> or <article>, recommend semantic landmarks."""
        inv_data = {
            "site": "https://testbrand.com",
            "infrastructure": {
                "llms_txt": {"status": 404, "present": False},
                "llms_full_txt": {"status": 404, "present": False},
                "robots": {"status": 200, "text": "User-agent: *\nAllow: /\n"},
            },
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": (
                        "<html><body><div class='wrapper'><div class='container'><div class='row'>"
                        + "<h1>TestBrand Home</h1>"
                        + "<p>Substantive text describing modern enterprise services across distributed cloud ecosystems. " * 15
                        + "</div></div></div></body></html>"
                    ),
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            ["python3", self.disc_script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        rec_ids = [r.get("id") for r in data.get("recommendations", [])]
        self.assertIn("PROACTIVE.DISCOVERY.SEMANTIC_LANDMARKS.001", rec_ids)
        self.assertIn("PROACTIVE.DISCOVERY.LLMS_TXT.001", rec_ids)

        self.assertIn("ai_agent_scrapeability_summary", data)
        summary = data["ai_agent_scrapeability_summary"]
        self.assertFalse(summary["semantic_landmarks_present"])


if __name__ == "__main__":
    unittest.main()
