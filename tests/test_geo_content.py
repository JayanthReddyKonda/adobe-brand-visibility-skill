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
        long_body = (
            "TestBrand provides comprehensive solutions for distributed systems and enterprise infrastructure. " * 20
        )
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

    def test_atomic_fact_to_token_ratio(self):
        # Text with low factual density (flowery marketing prose lacking numbers/dates)
        fluff = (
            "We are an innovative team that provides amazing solutions for incredible results. We strive to empower everyone with wonderful experiences. Our dedicated professionals work tirelessly to achieve marvelous outcomes."
            * 10
        )
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/about",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": f"<html><body><h1>About Us</h1><p>{fluff}</p></body></html>",
                }
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
        self.assertIn("LOW_FACT_TO_TOKEN_RATIO", cause_ids)

    def test_exophoric_pronoun_ratio(self):
        # Paragraphs opening with ambiguous pronouns
        p1 = "It enables seamless distributed workflow across cloud infrastructure without latency."
        p2 = "They provide comprehensive telemetry and observability for high-throughput enterprise pipelines."
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/features",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": f"<html><body><h1>Features</h1><p>{p1}</p><p>{p2}</p></body></html>",
                }
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
        rec_ids = [r.get("id") for r in data.get("recommendations", [])]
        self.assertIn("PROACTIVE.GEO.EXOPHORIC_PRONOUN_GROUNDING.001", rec_ids)

    def test_wilson_confidence_interval_calc(self):
        import sys

        sys.path.insert(0, os.path.dirname(self.script_path))
        from geo_content_check import wilson_confidence_interval

        # 10 runs, 5 citations (50% citation rate)
        low, high = wilson_confidence_interval(5, 10, z=1.96)
        self.assertTrue(0.20 < low < 0.35)
        self.assertTrue(0.65 < high < 0.80)
        # 0 total runs returns (0.0, 0.0)
        self.assertEqual(wilson_confidence_interval(0, 0), (0.0, 0.0))

    def test_qa_alone_format_warning(self):
        # Page with pure FAQ format lacking numbers, code, or comparisons
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/faq",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": "<html><body><h1>Frequently Asked Questions</h1><dl><dt>What do you do?</dt><dd>We assist customers with their workflows through intuitive interfaces.</dd><dt>How do I start?</dt><dd>Contact our team to get started with a consultation.</dd></dl></body></html>",
                }
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
        rec_ids = [r.get("id") for r in data.get("recommendations", [])]
        self.assertIn("PROACTIVE.GEO.BEYOND_FAQ_FORMAT.001", rec_ids)

    def test_page_improvement_plans_structure_and_epistemic_boundaries(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/overview",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": "<html><body><h1>Overview</h1><p>Our software delivers excellent results for modern development workflows and scalable platforms.</p></body></html>",
                }
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
        self.assertIn("page_improvement_plans", data)
        plans = data["page_improvement_plans"]
        self.assertGreaterEqual(len(plans), 1)

        plan = plans[0]
        self.assertEqual(plan["url"], "https://testbrand.com/overview")
        self.assertIn("citability_score", plan)
        self.assertIn("gap_analysis", plan)
        self.assertIn("prescribed_actions", plan)
        actions = plan["prescribed_actions"]
        self.assertIn("immediate_structural_actions", actions)
        self.assertIn("textual_modifications", actions)
        self.assertIn("passage_chunking_plan", actions)

        # Verify epistemic boundaries
        self.assertIn("epistemic_qualification", plan)
        qual = plan["epistemic_qualification"]
        self.assertIn("heuristic", qual.lower())
        self.assertTrue(
            "not live search engine citation logs" in qual or "not live engine citation logs" in qual or "guarantee" in qual.lower()
        )


if __name__ == "__main__":
    unittest.main()
