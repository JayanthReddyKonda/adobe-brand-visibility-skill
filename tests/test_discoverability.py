import json
import os
import subprocess
import tempfile
import unittest


class TestDiscoverabilityAudit(unittest.TestCase):
    def setUp(self):
        self.script_path = "src/skills/discoverability-audit/scripts/discoverability_check.py"
        self.test_inv = os.path.join(tempfile.gettempdir(), "test_disc_inv.json")

    def test_robots_txt_searchbot_blocking(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><head><title>Test</title><link rel='canonical' href='https://testbrand.com/'/></head><body><h1>Test</h1></body></html>",
                }
            ],
            "robots_txt": "User-agent: OAI-SearchBot\nDisallow: /\n",
            "sitemaps": [],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            ["python3", self.script_path, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "ok")
        cause_ids = [f.get("cause_id") for f in data.get("findings", [])]
        self.assertIn("AI_RETRIEVAL_BLOCKED", cause_ids)

    def test_clean_site_passes(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><head><title>Test</title><link rel='canonical' href='https://testbrand.com/'/></head><body><h1>Test</h1></body></html>",
                }
            ],
            "robots_txt": "User-agent: *\nAllow: /\n",
            "sitemaps": [],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            ["python3", self.script_path, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "ok")

    def test_rfc9309_oversized_robots(self):
        # Create oversized robots.txt (> 512,000 octets)
        huge_robots = "User-agent: *\nDisallow: /admin/\n" + ("# filler rule line\n" * 30000)
        inv_data = {
            "site": "https://testbrand.com",
            "robots_txt": huge_robots,
            "infrastructure": {"robots_status": 200},
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand</h1></body></html>",
                }
            ],
            "sitemaps": [],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script_path, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in data.get("findings", [])]
        self.assertIn("ROBOTS_TXT_OVERSIZED", cause_ids)

    def test_hf05_nosnippet_on_core_content(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand</h1></body></html>",
                },
                {
                    "url": "https://testbrand.com/article",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": '<html><head><meta name="robots" content="nosnippet"></head><body><h1>Guide</h1><p>Important details here.</p></body></html>',
                },
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script_path, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in data.get("findings", [])]
        self.assertIn("NOSNIPPET_ON_CORE_CONTENT", cause_ids)


if __name__ == "__main__":
    unittest.main()
