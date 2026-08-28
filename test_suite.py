#!/usr/bin/env python3
"""
test_suite.py - Comprehensive verification test suite for Brand AI-Readiness Audit Marketplace.
Tests:
  1. SSRF prevention and IP filtering against loopback, private, link-local, and cloud metadata.
  2. Crawler matrix semantics (training vs retrieval bot disallow rules).
  3. Scoped fact consistency and contradiction detection.
  4. Product lifecycle conflict detection (discontinued vs current).
  5. Mathematical Answerability Engine attribute coverage.
  6. Engagement orientation, intent-continuity, and information scent checks.
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
import audit_db



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
        self.assertEqual(critical_findings[0]["cause_id"], "AI_RETRIEVAL_BLOCKED")


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
        self.assertEqual(price_findings[0]["cause_id"], "FIRST_PARTY_FACT_CONFLICT")

    def test_product_lifecycle_conflict(self):
        page1 = """
        <html><head><title>Velocity X7 Legacy</title></head><body>
        <h1>Velocity X7 Drone</h1>
        <p>Discontinued Model: Velocity X7 is no longer in production.</p>
        </body></html>
        """
        page2 = """
        <html><head><title>Store Catalog</title></head><body>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Velocity X7 Drone",
          "offers": {
            "@type": "Offer",
            "price": "3999",
            "availability": "https://schema.org/InStock"
          }
        }
        </script>
        <h1>Velocity X7 Drone</h1>
        <p>In Stock - Buy Now</p>
        </body></html>
        """
        facts1 = fact_consistency_check.extract_scoped_facts(page1, "https://example.com/legacy/x7")
        facts2 = fact_consistency_check.extract_scoped_facts(page2, "https://example.com/store/x7")
        findings, recs = fact_consistency_check.evaluate_fact_consistency([facts1, facts2], "https://example.com")
        lc_findings = [f for f in findings if f["cause_id"] == "DISCONTINUED_VS_CURRENT_CONFLICT"]
        self.assertTrue(len(lc_findings) >= 1)


class TestEntityAnswerability(unittest.TestCase):
    def test_product_answerability(self):
        product_html = """
        <html><head><title>Garuda Velocity X9</title></head><body>
        <h1>Garuda Velocity X9</h1>
        <p>High performance drone with 4K camera and 30min flight time.</p>
        <p>Price: ₹5,499. Status: In Stock. Brand: Garuda Aerospace.</p>
        <button class="btn-cta">Buy Now</button>
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
        generic_h1 = [f for f in findings if f["cause_id"] == "LOW_INFORMATION_SCENT"]
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
        self.assertEqual(findings[0]["cause_id"], "AI_FACT_CONFLICT")
        self.assertEqual(findings[0]["severity"], "high")


class TestOrchestratorAndSchemaValidation(unittest.TestCase):
    def test_report_validation(self):
        # Strict clean production report schema
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
            "findings": [
                {
                    "id": "F-001",
                    "title": "Robots blocks retrieval",
                    "severity": "critical",
                    "category": "discoverability",
                    "root_cause": "Robots.txt blocks AI search bots",
                    "confidence": "high",
                    "evidence": "Disallow: / for OAI-SearchBot",
                    "suggested_action": {
                        "summary": "Allow OAI-SearchBot on public pages",
                        "priority": "critical"
                    }
                }
            ],
            "proactive_actions": [
                {
                    "title": "Publish sitemap.xml",
                    "summary": "Publish sitemap.xml to declare indexable pages",
                    "priority": "low"
                }
            ]
        }
        is_valid, errors = validate_report.validate_report_dict(report)
        self.assertTrue(is_valid, f"Validation errors: {errors}")



class TestResourceIsolationAndSitemaps(unittest.TestCase):
    def test_sitemap_xml_never_audited_as_product_page(self):
        """Invariant: Non-HTML resources (XML sitemaps) must NEVER enter page audits."""
        inv = {
            "base_url": "https://frescopa.coffee",
            "infrastructure": {
                "sitemaps_discovered": ["https://frescopa.coffee/sitemap.xml", "https://frescopa.coffee/sitemap-content.xml"],
                "sitemaps_processed": 2
            },
            "pages": [
                {
                    "url": "https://frescopa.coffee/",
                    "status": 200,
                    "resource_type": "html",
                    "page_type": "homepage",
                    "html": "<html><head><title>Frescopa Specialty Coffee Roasters</title></head><body><h1>Frescopa Fresh Coffee</h1><p>Artisanal coffee freshly roasted in small batches.</p></body></html>"
                },
                {
                    "url": "https://frescopa.coffee/sitemap-content.xml",
                    "status": 200,
                    "resource_type": "xml",
                    "page_type": "product",
                    "html": "<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>https://frescopa.coffee/products/espresso</loc></url></urlset>"
                }
            ]
        }

        # 1. Entity content check must ignore sitemap-content.xml
        e_res = entity_content_check.audit("https://frescopa.coffee", "frescopa.coffee", inv=inv)
        self.assertEqual(e_res["status"], "ok")
        sitemap_findings = [f for f in e_res.get("findings", []) if "sitemap" in f.get("evidence", "").lower() or "sitemap" in f.get("title", "").lower()]
        self.assertEqual(len(sitemap_findings), 0, "Sitemap XML was evaluated as a product page!")

        # 2. Engagement check must ignore sitemap-content.xml
        eng_res = engagement_check.audit("https://frescopa.coffee", "frescopa.coffee", inv=inv)
        self.assertEqual(eng_res["status"], "ok")
        sitemap_eng_findings = [f for f in eng_res.get("findings", []) if "sitemap" in f.get("evidence", "").lower() or "sitemap" in f.get("title", "").lower()]
        self.assertEqual(len(sitemap_eng_findings), 0, "Sitemap XML was evaluated in engagement check!")


class TestSQLiteAuditPersistence(unittest.TestCase):
    def test_sqlite_save_and_retrieve(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        try:
            # Clean report schema (no internal debugging dump)
            report = {
                "site": "example.com",
                "audited_at": "2026-08-28T15:00:00Z",
                "summary": {
                    "total_findings": 1,
                    "critical": 1,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "findings": [
                    {
                        "id": "F-001",
                        "title": "Robots blocked",
                        "severity": "critical",
                        "category": "discoverability",
                        "root_cause": "Robots.txt blocks AI search bots",
                        "confidence": "high",
                        "evidence": "Disallow: /",
                        "suggested_action": {
                            "summary": "Allow AI retrieval crawlers in robots.txt",
                            "priority": "critical"
                        }
                    }
                ],
                "proactive_actions": [
                    {
                        "title": "Add Organization JSON-LD",
                        "summary": "Publish schema.org Organization markup",
                        "priority": "low"
                    }
                ]
            }

            internal_telemetry = {
                "specialists": {
                    "discoverability-audit": {"label": "Access", "status": "ok"}
                },
                "execution_time_seconds": 1.5,
                "audit_metrics": {
                    "execution_time_seconds": 1.5,
                    "answerability_index": 0.95
                }
            }

            audit_id = audit_db.save_audit_report(report, internal_data=internal_telemetry, db_path=db_path)
            self.assertIsNotNone(audit_id)
            self.assertGreater(audit_id, 0)

            history = audit_db.list_recent_audits(db_path=db_path, limit=5)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["site"], "example.com")
            self.assertEqual(history[0]["critical_count"], 1)
            self.assertEqual(history[0]["total_findings"], 1)
            self.assertEqual(history[0]["execution_time_seconds"], 1.5)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)



class TestMultilingualContactAndGranularClassifier(unittest.TestCase):
    def test_contact_heading_multilingual_pass(self):
        # On a contact page, "Contáctenos" or "Contact us" is the exact intended heading and MUST NOT be flagged as defect
        html_es = """
        <html><head><title>Frescopa - Contáctenos</title></head><body>
        <h1>Contáctenos</h1>
        <p>Envíenos un mensaje o visítenos en nuestra tostaduría en Madrid.</p>
        <p>Email: soporte@frescopa.coffee | Tel: +34 912 345 678</p>
        <a href="/es/productos">Productos</a>
        <a href="/es/subscription">Suscripción</a>
        </body></html>
        """
        findings, recs, o_data = engagement_check.audit_page_engagement(html_es, "https://frescopa.coffee/es/contact", page_type="contact")
        h1_findings = [f for f in findings if f.get("cause_id") == "LOW_INFORMATION_SCENT"]
        self.assertEqual(len(h1_findings), 0, "Contact page with Contáctenos should not be flagged as low information scent")

    def test_granular_classifier_distinguishes_detail_and_listing(self):
        from acquire_inventory import classify_page
        pt1, conf1, tmpl1, loc1 = classify_page("https://frescopa.coffee/en/products/default")
        self.assertEqual(pt1, "template")

        pt2, conf2, tmpl2, loc2 = classify_page("https://frescopa.coffee/en/products")
        self.assertEqual(pt2, "product_listing")

        pt3, conf3, tmpl3, loc3 = classify_page("https://frescopa.coffee/en/products/ethiopia-yirgacheffe")
        self.assertEqual(pt3, "product_detail")

        pt4, conf4, tmpl4, loc4 = classify_page("https://frescopa.coffee/es/subscription")
        self.assertEqual(pt4, "subscription_flow")
        self.assertEqual(loc4, "es")


class TestSemanticFactLedgerExtraction(unittest.TestCase):
    def test_facts_extracted_from_headings_and_metadata(self):
        # Verify facts are extracted even on pure HTML sites without JSON-LD
        html = """
        <html><head>
        <title>Frescopa Artisanal Coffee</title>
        <meta property="og:site_name" content="Frescopa Coffee Roasters">
        <meta name="last-modified" content="2026-08-20">
        </head><body>
        <h1>Ethiopia Guji Single Origin</h1>
        <p>Specialty roasted coffee beans with notes of jasmine and bergamot.</p>
        <p>Price: $24.00 per 250g bag. In Stock.</p>
        <p>Contact: roastery@frescopa.coffee | +1-800-555-0199</p>
        <footer>© 2026 Frescopa Roasters</footer>
        </body></html>
        """
        facts = fact_consistency_check.extract_scoped_facts(html, "https://frescopa.coffee/products/guji")
        self.assertIn("Frescopa Coffee Roasters", facts["brand_names"])
        self.assertTrue(any(p["name"] == "Ethiopia Guji Single Origin" for p in facts["products_with_status"]))
        self.assertTrue(any(sp["price"] == "24" for sp in facts["scoped_prices"]))
        self.assertIn(2026, facts["copyright_years"])
        self.assertTrue(any(em["email"] == "roastery@frescopa.coffee" for em in facts["contact_emails"]))


if __name__ == "__main__":
    unittest.main()



