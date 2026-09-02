import json
import os
import subprocess
import tempfile
import unittest


class TestGeoContentAudit(unittest.TestCase):
    def setUp(self):
        self.script_path = "src/skills/geo-content-audit/scripts/geo_content_check.py"
        self.test_inv = os.path.join(tempfile.gettempdir(), "test_geo_inv.json")
        self.test_state = os.path.join(tempfile.gettempdir(), "test_geo_state.json")

    def test_geo_scoring(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand</h1><p>TestBrand accelerates workflow by 45% because our distributed cache eliminates disk I/O latency. Therefore, response times drop below 10ms.</p></body></html>",
                }
            ],
            "robots_txt": "",
            "sitemaps": [],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        with open(self.test_state, "w") as f:
            json.dump(
                {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}, f
            )

        res = subprocess.run(
            [
                "python3",
                self.script_path,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--state",
                self.test_state,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "ok")

    def test_geo_rag_passage_chunking_recommendation(self):
        long_body = "TestBrand provides comprehensive solutions for distributed systems and enterprise infrastructure. " * 20
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/overview",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": f"<html><body><p>{long_body}</p></body></html>",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script_path,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        rec_ids = [r.get("id") for r in data.get("recommendations", [])]
        self.assertIn("PROACTIVE.GEO.RAG_PASSAGE_CHUNKING.001", rec_ids)

    def test_hedge_language_density_detection(self):
        hedged_text = (
            "Our solution maybe provides some improvements. It seems to help roughly 50 users and appears to be "
            "fairly useful. In some ways, it could possibly improve workflow because it tends to reduce latency. "
            "Generally, it might sort of be a bit faster than legacy tools in most cases."
        ) * 3
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/overview",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": f"<html><body><h1>Overview</h1><p>{hedged_text}</p></body></html>",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script_path,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in data.get("findings", [])]
        self.assertIn("EXCESSIVE_HEDGE_LANGUAGE", cause_ids)

    def test_content_recency_detection(self):
        long_body = "Generative Engine Optimization evaluates passage chunking and recency signals. " * 25
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/stale-guide",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": f"<html><head><meta property='article:modified_time' content='2023-01-01T00:00:00Z'></head><body><h1>Stale Guide</h1><p>{long_body}</p></body></html>",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script_path,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in data.get("findings", [])]
        self.assertIn("CONTENT_RECENCY_DEFICIT", cause_ids)


if __name__ == "__main__":
    unittest.main()
