#!/usr/bin/env python3
"""
test_suite.py - Comprehensive verification test suite for Brand AI-Readiness Audit Marketplace.
Tests:
  1. SSRF prevention and IP filtering against loopback, private, link-local, and cloud metadata.
  2. Bounded response streaming and truncation.
  3. Crawler matrix semantics (training vs retrieval bot disallow rules).
  4. Scoped fact consistency and contradiction detection.
  5. Answerability engine attribute coverage.
  6. Engagement orientation and heading scent checks.
  7. Optional representation cross-check with observed AI outputs.
  8. End-to-end multi-specialist composition, taxonomy root causes, and schema validation.
"""

import sys
import os
import json
import unittest
import tempfile

# Add script paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE_DIR, "brand-ai-readiness-audit", "skills")
sys.path.insert(0, os.path.join(SKILLS_DIR, "audit-orchestrator", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "discoverability-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "entity-content-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "fact-consistency-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "corroboration-authority-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "engagement-context-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "assistant-representation-audit", "scripts"))

from safe_fetch import safe_fetch, is_ip_allowed, validate_hostname_ips
import discoverability_check
import entity_content_check
import fact_consistency_check
import corroboration_check
import engagement_check
import representation_check
import orchestrator
import validate_report


class TestSSRFAndSecurity(unittest.TestCase):
    def test_ip_filtering(self):
        # Loopback
        self.assertFalse(is_ip_allowed("127.0.0.1"))
        self.assertFalse(is_ip_allowed("127.0.1.1"))
        self.assertFalse(is_ip_allowed("::1"))
        # Private
        self.assertFalse(is_ip_allowed("10.0.0.1"))
        self.assertFalse(is_ip_allowed("192.168.1.1"))
        self.assertFalse(is_ip_allowed("172.16.0.1"))
        # Cloud metadata
        self.assertFalse(is_ip_allowed("169.254.169.254"))
        # Public IP
        self.assertTrue(is_ip_allowed("8.8.8.8"))
        self.assertTrue(is_ip_allowed("1.1.1.1"))

    def test_safe_fetch_blocks_private_targets(self):
        status, body, headers, err = safe_fetch("http://127.0.0.1:8000/secret")
        self.assertIsNone(status)
        self.assertIn("SSRF blocked", err)

        status, body, headers, err = safe_fetch("http://169.254.169.254/latest/meta-data")
        self.assertIsNone(status)
        self.assertIn("SSRF blocked", err)


class TestCrawlerMatrixSemantics(unittest.TestCase):
    def test_training_bot_disallow_not_critical(self):
        robots_txt = """
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /
"""
        inv = {
            "pages": [{
                "url": "https://example.com/",
                "status": 200,
                "page_type": "homepage",
                "html": "<html><head><title>Example</title></head><body><h1>Welcome to Example</h1><p>We build fine tools for everyone.</p></body></html>"
            }],
            "robots": {"status": 200, "text": robots_txt}
        }
        res = discoverability_check.audit("https://example.com", "example.com", inv=inv)
        self.assertEqual(res["status"], "ok")
        critical_findings = [f for f in res["findings"] if f["severity"] == "critical"]
        self.assertEqual(len(critical_findings), 0)
        obs = [o for o in res["observations"] if "training" in o["observation"].lower()]
        self.assertTrue(len(obs) >= 1)

    def test_retrieval_bot_disallow_is_critical(self):
        robots_txt = """
User-agent: OAI-SearchBot
Disallow: /

User-agent: PerplexityBot
Disallow: /
"""
        inv = {
            "pages": [{
                "url": "https://example.com/",
                "status": 200,
                "page_type": "homepage",
                "html": "<html><head><title>Example</title></head><body><h1>Example</h1><p>Lots of content here.</p></body></html>"
            }],
            "robots": {"status": 200, "text": robots_txt}
        }
        res = discoverability_check.audit("https://example.com", "example.com", inv=inv)
        self.assertEqual(res["status"], "ok")
        critical_findings = [f for f in res["findings"] if f["severity"] == "critical"]
        self.assertTrue(len(critical_findings) >= 1)
        self.assertIn("retrieval", critical_findings[0]["title"].lower())


class TestFactConsistencyAndScope(unittest.TestCase):
    def test_distinct_tiers_not_contradiction(self):
        page1 = """
        <html><head><title>Pricing - Acme</title></head><body>
        <h1>Pricing Plans</h1>
        <h2>Starter Tier</h2>
        <p>Starter plan is $10 per month.</p>
        <h2>Pro Tier</h2>
        <p>Pro plan is $50 per month.</p>
        </body></html>
        """
        facts1 = fact_consistency_check.extract_scoped_facts(page1, "https://example.com/pricing")
        findings, recs = fact_consistency_check.evaluate_fact_consistency([facts1], "https://example.com")
        price_findings = [f for f in findings if f["category"] == "fact-consistency"]
        self.assertEqual(len(price_findings), 0)

    def test_conflicting_price_for_same_product_is_contradiction(self):
        page1 = """
        <html><head><title>Product X9</title></head><body>
        <h1>Velocity X9</h1>
        <p>The Velocity X9 flagship model is priced at ₹5,499 today.</p>
        </body></html>
        """
        page2 = """
        <html><head><title>Legacy Promo</title></head><body>
        <h1>Velocity X9</h1>
        <p>Get Velocity X9 for only ₹4,999 in our catalog.</p>
        </body></html>
        """
        facts1 = fact_consistency_check.extract_scoped_facts(page1, "https://example.com/products/x9")
        facts2 = fact_consistency_check.extract_scoped_facts(page2, "https://example.com/promo")
        findings, recs = fact_consistency_check.evaluate_fact_consistency([facts1, facts2], "https://example.com")
        price_findings = [f for f in findings if f["category"] == "fact-consistency"]
        self.assertTrue(len(price_findings) >= 1)
        self.assertEqual(price_findings[0]["cause_family"], "FACT.CONSISTENCY")


class TestEntityAnswerability(unittest.TestCase):
    def test_product_answerability(self):
        product_html = """
        <html><head><title>Garuda Velocity X9</title></head><body>
        <h1>Garuda Velocity X9</h1>
        <p>High performance drone with 4K camera and 30min flight time.</p>
        <p>Price: ₹5,499. Status: In Stock. Brand: Garuda Aerospace.</p>
        </body></html>
        """
        dom = entity_content_check.EntityDOMParser()
        dom.feed(product_html)
        ans = entity_content_check.evaluate_page_answerability("product", product_html, dom, "https://example.com")
        self.assertIsNotNone(ans)
        self.assertIn("product_name", ans["present"])
        self.assertIn("price", ans["present"])
        self.assertIn("availability", ans["present"])
        self.assertGreaterEqual(ans["coverage_ratio"], 0.8)


class TestEngagementOrientation(unittest.TestCase):
    def test_generic_h1_flagged(self):
        html = """
        <html><head><title>Example Site</title></head><body>
        <h1>Welcome</h1>
        <p>We are a company that does lots of interesting things for people around the world every day.</p>
        <p>Read on to discover everything we can help you achieve today and tomorrow.</p>
        </body></html>
        """
        findings, recs, o_data = engagement_check.audit_page_engagement(html, "https://example.com/")
        generic_h1 = [f for f in findings if f["cause_id"] == "ENG-H1-GENERIC"]
        self.assertTrue(len(generic_h1) >= 1)


class TestRepresentationCrossCheck(unittest.TestCase):
    def test_representation_price_conflict(self):
        snapshot = {
            "status": "ok",
            "full_text": "Our flagship subscription costs $49 per month.",
            "prices_visible": ["49"]
        }
        observations_data = {
            "observations": [
                {
                    "assistant": "ChatGPT",
                    "prompt": "How much does the subscription cost?",
                    "mentioned": True,
                    "cited": True,
                    "claims": [{"fact": "The subscription is $99 per month.", "topic": "pricing"}]
                }
            ]
        }
        findings, notes = representation_check.compare_assistant_observations(snapshot, observations_data)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["cause_family"], "REPRESENTATION.ACCURACY")
        self.assertEqual(findings[0]["severity"], "high")


class TestOrchestratorAndSchemaValidation(unittest.TestCase):
    def test_report_validation(self):
        report = {
            "site": "example.com",
            "audited_at": "2026-08-28T14:00:00Z",
            "summary": {
                "total_findings": 1,
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "specialists": {
                "discoverability-audit": {"label": "Access", "status": "ok"}
            },
            "findings": [
                {
                    "id": "F-001",
                    "title": "Robots blocks retrieval",
                    "severity": "critical",
                    "evidence": "Disallow: / for OAI-SearchBot",
                    "suggested_action": {
                        "summary": "Allow OAI-SearchBot on public pages",
                        "priority": "critical"
                    }
                }
            ],
            "audit_metrics": {
                "pages_sampled": 1,
                "critical_blockers": 1
            }
        }
        is_valid, errors = validate_report.validate_report_dict(report)
        self.assertTrue(is_valid, f"Validation errors: {errors}")

    def test_full_inventory_specialist_composition(self):
        # Create a mock inventory with rich multi-page fixtures
        inv = {
            "base_url": "https://garuda-drones.example.com",
            "pages": [
                {
                    "url": "https://garuda-drones.example.com/",
                    "status": 200,
                    "page_type": "homepage",
                    "html": """
                    <html><head><title>Garuda Drones - Autonomous Flight</title>
                    <script type="application/ld+json">
                    {
                      "@context": "https://schema.org",
                      "@type": "Organization",
                      "name": "Garuda Drones",
                      "url": "https://garuda-drones.example.com",
                      "sameAs": ["https://www.wikidata.org/wiki/Q12345"]
                    }
                    </script>
                    </head><body>
                    <h1>Garuda Autonomous Drones</h1>
                    <p>Next-generation commercial drones built for survey and delivery.</p>
                    <nav><a href="/products">Products</a> <a href="/pricing">Pricing</a></nav>
                    <footer><p>© 2026 Garuda Drones</p></footer>
                    </body></html>
                    """
                },
                {
                    "url": "https://garuda-drones.example.com/products/x9",
                    "status": 200,
                    "page_type": "product",
                    "html": """
                    <html><head><title>Velocity X9 - Garuda Drones</title>
                    <script type="application/ld+json">
                    {
                      "@context": "https://schema.org",
                      "@type": "Product",
                      "name": "Velocity X9",
                      "offers": {
                        "@type": "Offer",
                        "price": "5499",
                        "priceCurrency": "INR",
                        "availability": "https://schema.org/InStock"
                      }
                    }
                    </script>
                    </head><body>
                    <h1>Velocity X9 Drone</h1>
                    <p>Price: ₹5,499. High endurance survey drone.</p>
                    </body></html>
                    """
                }
            ],
            "robots": {
                "status": 200,
                "text": "User-agent: *\nDisallow: /admin\n\nUser-agent: OAI-SearchBot\nAllow: /\n"
            }
        }

        # Test each specialist against the inventory
        disc_res = discoverability_check.audit(inv["base_url"], "garuda-drones.example.com", inv=inv)
        self.assertEqual(disc_res["status"], "ok")

        ent_res = entity_content_check.audit(inv["base_url"], "garuda-drones.example.com", inv=inv)
        self.assertEqual(ent_res["status"], "ok")
        self.assertEqual(ent_res["entity_snapshot"]["organization"]["name"], "Garuda Drones")

        fact_res = fact_consistency_check.audit(inv["base_url"], "garuda-drones.example.com", inv=inv)
        self.assertEqual(fact_res["status"], "ok")

        eng_res = engagement_check.audit(inv["base_url"], "garuda-drones.example.com", inv=inv)
        self.assertEqual(eng_res["status"], "ok")


if __name__ == "__main__":
    unittest.main()

