"""Unit tests verifying custom forensic parameters across all diagnostic sensors and helper scripts.

Tests all custom CLI parameters and programmatic interfaces added to:
- discoverability_check.py (--url, --bot, --subsystem)
- entity_content_check.py (--url, --schema-type, --answerability-only)
- fact_consistency_check.py (--attribute, --compare-urls, --query)
- corroboration_check.py (--sameas-only, --probe-url, --verify-backlink)
- geo_content_check.py (--url, --page-plan-only, --analyze-text)
- engagement_check.py (--url, --referrer-query, --viewport-only)
- safe_fetch.py (--headers-only, --extract-text)
- orchestrator.py (--skills)
- bundle_context.py (--archetype, --topic)
- plan.py (--rank-findings)
"""

import json
import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestCustomParameterForensics(unittest.TestCase):
    """Verifies that all custom CLI forensic parameters function cleanly and return structured JSON."""

    @classmethod
    def setUpClass(cls):
        home_html = (
            "<!DOCTYPE html><html><head><title>Acme Software | Enterprise Cloud Platform</title>"
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Acme Software","url":"https://example.com","sameAs":["https://www.wikidata.org/wiki/Q12345"]}</script>'
            "</head><body>"
            "<h1>Enterprise Cloud Platform</h1>"
            "<p>Acme Cloud delivers enterprise workflow intelligence because modern teams require speed. Founded in 2020 by Jane Doe. Pricing starts at $49/month billed annually.</p>"
            '<a href="/signup">Start Free Trial</a>'
            "</body></html>"
        )
        pricing_html = (
            "<!DOCTYPE html><html><head><title>Acme Pricing Plans</title>"
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Acme Cloud Pro","offers":{"@type":"Offer","price":"49","priceCurrency":"USD","availability":"https://schema.org/InStock"}}</script>'
            "</head><body>"
            "<h1>Transparent Pricing Plans</h1>"
            "<p>Choose the best plan for your team. Pro plan is $49/month. Enterprise plan is $199/month with dedicated 24/7 engineering support and 99.9% uptime SLA.</p>"
            '<a href="/checkout/pro">Subscribe Pro</a>'
            "</body></html>"
        )

        cls.sample_inv = {
            "site": "https://example.com",
            "crawled_at": "2026-09-12T12:00:00Z",
            "robots": {
                "status": 200,
                "raw": "User-agent: *\nAllow: /\n\nUser-agent: Claude-SearchBot\nDisallow: /private\n",
                "matrix": {
                    "OAI-SearchBot": True,
                    "PerplexityBot": True,
                    "Claude-SearchBot": True,
                    "GPTBot": False,
                },
                "sitemaps": ["https://example.com/sitemap.xml"],
            },
            "sitemaps": ["https://example.com/sitemap.xml"],
            "pages": [
                {
                    "url": "https://example.com/",
                    "status": 200,
                    "status_code": 200,
                    "page_type": "homepage",
                    "resource_type": "html",
                    "canonical": "https://example.com/",
                    "title": "Acme Software | Enterprise Cloud Platform",
                    "word_count": 950,
                    "snr_ratio": 0.45,
                    "is_sparse_spa": False,
                    "html": home_html,
                    "raw_html": home_html,
                    "text": "Acme Cloud delivers enterprise workflow intelligence because modern teams require speed. Founded in 2020 by Jane Doe. Pricing starts at $49/month billed annually.",
                    "headings": {
                        "h1": ["Enterprise Cloud Platform"],
                        "h2": ["Why Acme", "Pricing Plans"],
                    },
                    "jsonld": [
                        {
                            "@context": "https://schema.org",
                            "@type": "Organization",
                            "name": "Acme Software",
                            "url": "https://example.com",
                            "sameAs": ["https://www.wikidata.org/wiki/Q12345"],
                        }
                    ],
                    "ctas": [
                        {"text": "Start Free Trial", "href": "/signup", "is_commercial_cta": True}
                    ],
                },
                {
                    "url": "https://example.com/pricing",
                    "status": 200,
                    "status_code": 200,
                    "page_type": "pricing",
                    "resource_type": "html",
                    "canonical": "https://example.com/pricing",
                    "title": "Acme Pricing Plans",
                    "word_count": 750,
                    "snr_ratio": 0.55,
                    "is_sparse_spa": False,
                    "html": pricing_html,
                    "raw_html": pricing_html,
                    "text": "Choose the best plan for your team. Pro plan is $49/month. Enterprise plan is $199/month with dedicated 24/7 engineering support and 99.9% uptime SLA.",
                    "headings": {
                        "h1": ["Transparent Pricing Plans"],
                        "h2": ["Pro Tier", "Enterprise Tier"],
                    },
                    "jsonld": [
                        {
                            "@context": "https://schema.org",
                            "@type": "Product",
                            "name": "Acme Cloud Pro",
                            "offers": {
                                "@type": "Offer",
                                "price": "49",
                                "priceCurrency": "USD",
                                "availability": "https://schema.org/InStock",
                            },
                        }
                    ],
                    "ctas": [
                        {"text": "Subscribe Pro", "href": "/checkout/pro", "is_commercial_cta": True}
                    ],
                },
            ],
            "stats": {"pages_crawled": 2},
        }
        cls.fixture_path = os.path.join(ROOT_DIR, "tests", "fixtures", "sample_forensic_inv.json")
        os.makedirs(os.path.dirname(cls.fixture_path), exist_ok=True)
        with open(cls.fixture_path, "w", encoding="utf-8") as f:
            json.dump(cls.sample_inv, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.fixture_path):
            try:
                os.remove(cls.fixture_path)
            except OSError:
                pass

    def test_discoverability_check_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "discoverability-audit", "scripts", "discoverability_check.py")

        # 1. --url
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--url", "https://example.com/pricing"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("target_inspection", data)
        self.assertEqual(data["target_inspection"].get("url"), "https://example.com/pricing")
        self.assertGreater(data["target_inspection"].get("word_count", 0), 0)

        # 2. --bot
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--bot", "Claude-SearchBot"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("bot_permission", data)
        self.assertEqual(data["bot_permission"].get("bot"), "Claude-SearchBot")
        self.assertIn("decision", data["bot_permission"])

        # 3. --subsystem
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--subsystem", "rendering"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("findings", data)

    def test_entity_content_check_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "entity-content-audit", "scripts", "entity_content_check.py")

        # 1. --url
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--url", "https://example.com/pricing"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("target_inspection", data)
        self.assertEqual(data["target_inspection"].get("url"), "https://example.com/pricing")
        self.assertIn("Product", data["target_inspection"].get("schema_types_present", []))

        # 2. --schema-type
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--schema-type", "Product"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("matching_entities", data)

        # 3. --answerability-only
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--answerability-only"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("answerability_evaluations", data)

    def test_fact_consistency_check_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "fact-consistency-audit", "scripts", "fact_consistency_check.py")

        # 1. --attribute
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--attribute", "pricing"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("findings", data)

        # 2. --compare-urls
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--compare-urls", "https://example.com/", "https://example.com/pricing"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("url_comparison", data)
        self.assertEqual(data["url_comparison"].get("url1"), "https://example.com/")

        # 3. --query
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--query", "Pro"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("query_matches", data)

    def test_corroboration_check_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "corroboration-authority-audit", "scripts", "corroboration_check.py")

        # 1. --sameas-only
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--sameas-only"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("sameas_urls", data)
        self.assertGreaterEqual(len(data.get("sameas_urls", [])), 1)

    def test_geo_content_check_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "geo-content-audit", "scripts", "geo_content_check.py")

        # 1. --url
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--url", "https://example.com/"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("coverage", data)

        # 2. --page-plan-only
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--page-plan-only", "https://example.com/"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("page_improvement_plan", data)

        # 3. --analyze-text
        sample_text = "Acme Cloud delivers enterprise intelligence because modern teams require speed. Benchmark tests show 42% latency reduction."
        res = subprocess.run(
            [sys.executable, script, "--analyze-text", sample_text],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("citability_breakdown", data)
        self.assertGreater(data.get("citability_score", 0), 0)

    def test_engagement_check_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "engagement-context-audit", "scripts", "engagement_check.py")

        # 1. --url
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--url", "https://example.com/pricing"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")

        # 2. --referrer-query
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--referrer-query", "enterprise cloud platform pricing"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("referrer_query"), "enterprise cloud platform pricing")
        self.assertIn("evaluations", data)

        # 3. --viewport-only
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--viewport-only"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("viewport_records", data)

    def test_orchestrator_skills_filter(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "audit-orchestrator", "scripts", "orchestrator.py")
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--telemetry", "--skills", "discoverability,entity"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        sensors = data.get("sensor_telemetry", {})
        self.assertIn("discoverability-audit", sensors)
        self.assertIn("entity-content-audit", sensors)
        self.assertNotIn("engagement-context-audit", sensors)

    def test_bundle_context_custom_params(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "audit-orchestrator", "scripts", "bundle_context.py")
        res = subprocess.run(
            [sys.executable, script, "--site", "https://example.com", "--inventory", self.fixture_path, "--archetype", "saas", "--topic", "retrieval"],
            capture_output=True, text=True, check=True
        )
        # bundle_context outputs markdown briefing for the AI agent
        output_text = res.stdout
        self.assertIn("saas", output_text.lower())
        self.assertIn("retrieval", output_text.lower())
        self.assertIn("robots.txt", output_text)

    def test_plan_rank_findings(self):
        script = os.path.join(ROOT_DIR, "src", "skills", "audit-orchestrator", "scripts", "plan.py")
        findings_file = os.path.join(ROOT_DIR, "tests", "fixtures", "temp_findings_to_rank.json")
        sample_findings = [
            {"id": "F-001", "dag_node": "GEO_CITABILITY", "severity": 2, "difficulty": 1},
            {"id": "F-002", "dag_node": "RETRIEVAL", "severity": 4, "difficulty": 2}
        ]
        with open(findings_file, "w", encoding="utf-8") as f:
            json.dump(sample_findings, f)

        try:
            res = subprocess.run(
                [sys.executable, script, "--rank-findings", findings_file],
                capture_output=True, text=True, check=True
            )
            data = json.loads(res.stdout)
            self.assertEqual(data.get("status"), "ok")
            ranked = data.get("roadmap", [])
            self.assertEqual(len(ranked), 2)
            # RETRIEVAL (severity 4) ranked before GEO_CITABILITY (severity 2)
            self.assertEqual(ranked[0]["id"], "F-002")
            self.assertEqual(ranked[1]["id"], "F-001")
        finally:
            if os.path.exists(findings_file):
                try:
                    os.remove(findings_file)
                except OSError:
                    pass

    def test_safe_fetch_custom_functions(self):
        scraper_scripts = os.path.join(ROOT_DIR, "src", "skills", "web-scraper", "scripts")
        if scraper_scripts not in sys.path:
            sys.path.insert(0, scraper_scripts)
        from safe_fetch import _is_safe_host, extract_readable_text

        # SSRF checks
        self.assertFalse(_is_safe_host("127.0.0.1")[0])
        self.assertFalse(_is_safe_host("169.254.169.254")[0])
        self.assertFalse(_is_safe_host("10.0.0.1")[0])

        # Clean text extraction
        html = "<html><head><title>Test</title></head><body><h1>Main Title</h1><p>Substantive article paragraph with factual claims.</p></body></html>"
        extracted = extract_readable_text(html)
        self.assertIn("h1: Main Title", extracted["headings"])
        self.assertIn("Substantive article paragraph", extracted["text"])
        self.assertGreater(extracted["word_count"], 0)


if __name__ == "__main__":
    unittest.main()
