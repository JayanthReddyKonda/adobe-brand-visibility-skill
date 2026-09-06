import json
import os
import subprocess
import tempfile
import unittest


class TestEngagementDeep(unittest.TestCase):
    def setUp(self):
        self.script = "src/skills/engagement-context-audit/scripts/engagement_check.py"
        self.test_inv = os.path.join(tempfile.gettempdir(), "test_eng_inv.json")
        self.test_state = os.path.join(tempfile.gettempdir(), "test_eng_state.json")

    def test_engagement_audit_execution(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/pricing",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "pricing",
                    "html": '<html><body><h1>Pricing Plans</h1><p>Plans start at $49/mo.</p><a href="/signup">Sign Up</a></body></html>',
                }
            ],
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
                self.script,
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
        out = json.loads(res.stdout)
        self.assertEqual(out["status"], "ok")

    def test_product_detail_scent_anchoring(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/products/pro",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "product_detail",
                    "html": '<html><body><h1>Enterprise Pro Suite</h1><p>Details about enterprise pro suite.</p><a href="/checkout">Buy Now</a></body></html>',
                }
            ],
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
                self.script,
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
        out = json.loads(res.stdout)
        self.assertEqual(out["status"], "ok")

    def test_empty_pages_engagement_handling(self):
        inv_data = {"site": "https://testbrand.com", "pages": []}
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

    def test_recommendation_on_missing_heading_scent(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><p>No headings anywhere on this page.</p></body></html>",
                }
            ],
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
                self.script,
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
        out = json.loads(res.stdout)
        recs = [r.get("title") for r in out.get("recommendations", [])]
        self.assertTrue(any("h1" in r.lower() or "heading" in r.lower() for r in recs))

    def test_state_population_by_engagement(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand Official</h1><p>Contact: support@testbrand.com</p></body></html>",
                }
            ],
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
                self.script,
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

    def test_agent_interaction_barrier_div_onclick(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/portal",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "product_detail",
                    "html": '<html><body><h1>TestBrand</h1><div onclick="checkout()">Buy</div><div onclick="pay()">Pay</div><div onclick="submit()">Submit</div></body></html>',
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        cause_ids = [f.get("cause_id") for f in out.get("findings", [])]
        self.assertIn("AGENT_INTERACTION_BARRIER", cause_ids)

    def test_weak_cta_detection(self):
        long_body = "Explore our cloud native solutions and distributed databases. " * 15
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": f"<html><body><h1>Cloud Platform</h1><p>{long_body}</p><button>Submit</button></body></html>",
                }
            ],
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        rec_ids = [r.get("id") for r in out.get("recommendations", [])]
        self.assertIn("PROACTIVE.ENGAGEMENT.VALUE_DRIVEN_CTA.001", rec_ids)

    def test_pricing_manifest_probe(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand</h1><p>Pricing starts at $29/mo.</p></body></html>",
                }
            ],
            "infrastructure": {"pricing_manifest": {"present": True, "status": 200, "snippet": "# Pricing"}},
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        obs = [o.get("observation", "") for o in out.get("observations", [])]
        self.assertTrue(any("Found machine-readable /pricing.md manifest" in o for o in obs))

    def test_heuristic_only_limitation_present_without_analytics(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "homepage",
                    "html": "<html><body><h1>TestBrand</h1><p>Welcome to our cloud solutions.</p><a href='/contact'>Contact Us</a></body></html>",
                }
            ],
            "infrastructure": {"pricing_manifest": {"present": True}},
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)
        res = subprocess.run(
            ["python3", self.script, "--site", "https://testbrand.com", "--inventory", self.test_inv],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertIn("analytics_summary", out)
        summary = out["analytics_summary"]
        self.assertFalse(summary["first_party_analytics_provided"])
        self.assertIn("limitations", out)
        self.assertTrue(any("static HTML layout proxies" in lim for lim in out["limitations"]))

    def test_analytics_ingestion_and_corroboration(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/pricing",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "pricing",
                    "html": "<html><body><h1>Pricing</h1><p>Vague text lacking prices.</p><a href='/demo'>Demo</a></body></html>",
                }
            ],
            "infrastructure": {"pricing_manifest": {"present": True}},
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        analytics_file = os.path.join(tempfile.gettempdir(), "test_analytics_high_bounce.json")
        analytics_data = [
            {
                "route": "/pricing",
                "sessions": 120,
                "ai_referral_bounce_rate": 0.78,
                "organic_bounce_rate": 0.40,
                "bounce_rate": 0.78,
                "avg_dwell_time_seconds": 14,
                "primary_referrer": "chatgpt.com",
            }
        ]
        with open(analytics_file, "w") as f:
            json.dump(analytics_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--analytics",
                analytics_file,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertIn("analytics_summary", out)
        self.assertTrue(out["analytics_summary"]["first_party_analytics_provided"])
        self.assertEqual(out["analytics_summary"]["pages_with_analytics"], 1)

        # Must trigger AI_REFERRAL_DISCONTINUITY
        cause_ids = [f.get("cause_id") for f in out.get("findings", [])]
        self.assertIn("AI_REFERRAL_DISCONTINUITY", cause_ids)

    def test_analytics_healthy_retention_mitigation(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [
                {
                    "url": "https://testbrand.com/pricing",
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "pricing",
                    "html": "<html><body><h1>Pricing</h1><div onclick='a()'>Btn 1</div><div onclick='b()'>Btn 2</div><div onclick='c()'>Btn 3</div></body></html>",
                }
            ],
            "infrastructure": {"pricing_manifest": {"present": True}},
        }
        with open(self.test_inv, "w") as f:
            json.dump(inv_data, f)

        analytics_file = os.path.join(tempfile.gettempdir(), "test_analytics_healthy.json")
        analytics_data = [
            {
                "route": "/pricing",
                "sessions": 250,
                "bounce_rate": 0.18,
                "avg_dwell_time_seconds": 115,
                "primary_referrer": "perplexity.ai",
            }
        ]
        with open(analytics_file, "w") as f:
            json.dump(analytics_data, f)

        res = subprocess.run(
            [
                "python3",
                self.script,
                "--site",
                "https://testbrand.com",
                "--inventory",
                self.test_inv,
                "--analytics",
                analytics_file,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertIn("analytics_summary", out)
        self.assertTrue(out["analytics_summary"]["first_party_analytics_provided"])
        self.assertGreaterEqual(out["analytics_summary"]["mitigated_findings_count"], 1)
        # Verify evidence mentions mitigation
        evidences = [f.get("evidence", "") for f in out.get("findings", [])]
        self.assertTrue(any("Mitigated by Analytics" in e for e in evidences))


if __name__ == "__main__":
    unittest.main()
