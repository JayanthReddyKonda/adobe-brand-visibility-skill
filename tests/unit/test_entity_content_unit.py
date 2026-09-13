"""Unit tests for Entity Identity & Content Answerability sensor."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "entity-content-audit", "scripts")
for p in [PROJECT_ROOT, SKILL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import entity_content_check

from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_empty_inventory,
    make_healthy_inventory,
)


class TestEntityContentUnit(unittest.TestCase):
    """Verifies entity understanding, microdata/RDFa extraction, and commercial answerability scoring."""

    def test_extract_product_microdata(self):
        """Success test: Microdata Product markup extracted accurately."""
        html = """
        <div itemscope itemtype="https://schema.org/Product">
            <h1 itemprop="name">Enterprise Cloud Suite</h1>
            <span itemprop="sku">ECS-100</span>
            <p itemprop="description">Scalable enterprise cloud platform.</p>
        </div>
        """
        entities = entity_content_check.extract_microdata_and_rdfa(html)
        self.assertEqual(len(entities), 1)
        prod = entities[0]
        self.assertEqual(prod.get("@type"), "Product")
        self.assertEqual(prod.get("name"), "Enterprise Cloud Suite")
        self.assertEqual(prod.get("sku"), "ECS-100")

    def test_extract_organization_rdfa(self):
        """Success test: RDFa Organization markup extracted accurately."""
        html = """
        <div vocab="https://schema.org/" typeof="Organization">
            <span property="name">Acme Corporation</span>
            <a property="url" href="https://acme.com">Website</a>
        </div>
        """
        entities = entity_content_check.extract_microdata_and_rdfa(html)
        self.assertEqual(len(entities), 1)
        org = entities[0]
        self.assertEqual(org.get("@type"), "Organization")
        self.assertEqual(org.get("name"), "Acme Corporation")

    def test_audit_healthy_site_detects_entities(self):
        """Success test: Site with Schema.org Organization and Product passes entity check."""
        inv = make_healthy_inventory("https://example.com")
        res = entity_content_check.audit("https://example.com", "example.com", inv)
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertNotIn("MATERIAL_ENTITY_AMBIGUITY", cause_ids)

    def test_audit_defective_site_flags_entity_ambiguity(self):
        """Failure test: Site lacking structured entity markup flags MATERIAL_ENTITY_AMBIGUITY."""
        inv = make_defective_inventory("https://example.com")
        res = entity_content_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertIn("MATERIAL_ENTITY_AMBIGUITY", cause_ids)

    def test_audit_flags_non_text_fact_locking(self):
        """Failure test: Critical commercial charts in un-annotated raster images flag MISSING_MATERIAL_FACT."""
        inv = {
            "site": "https://example.com",
            "crawled_at": "2026-09-06T12:00:00Z",
            "pages": [
                {
                    "url": "https://example.com/pricing",
                    "page_type": "pricing",
                    "html": "<html><body><h1>Pricing</h1><img src='/images/pricing-table-chart.png' alt='pricing' /></body></html>",
                    "images": [{"src": "/images/pricing-table-chart.png", "alt": "pricing", "class": "", "id": ""}],
                }
            ],
        }
        res = entity_content_check.audit("https://example.com", "example.com", inv)
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertIn("MISSING_MATERIAL_FACT", cause_ids)

    def test_audit_empty_inventory_handled_safely(self):
        """Boundary/Failure test: Empty inventory handled gracefully."""
        inv = make_empty_inventory("https://example.com")
        res = entity_content_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIsInstance(res.get("findings"), list)

    def test_evaluate_page_answerability_product_detail(self):
        """Verify answerability scoring on product_detail uses MATERIAL_ATTRIBUTE_WEIGHTS."""
        html = "<html><body><h1>Cloud Pro Server</h1><p>High performance cluster.</p></body></html>"
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        entities = [
            {
                "@type": "Product",
                "name": "Cloud Pro Server",
                "sku": "CPS-100",
                "description": "High performance cluster.",
                "offers": {"@type": "Offer", "price": "99.00", "availability": "https://schema.org/InStock"},
            }
        ]
        ans = entity_content_check.evaluate_page_answerability("product_detail", html, dom, "https://example.com/p", entities)
        self.assertEqual(ans["status"], "present")
        results = ans["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["score"], 1.0)
        self.assertTrue(results[0]["facts"]["product_name"])
        self.assertTrue(results[0]["facts"]["price"])
        self.assertTrue(results[0]["facts"]["availability"])
        self.assertTrue(results[0]["facts"]["specifications"])

    def test_evaluate_page_answerability_pricing(self):
        """Verify answerability scoring for pricing pages extracting facts from DOM and JSON-LD."""
        html = """
        <html><body>
            <h1>Pricing Plans</h1>
            <p>Starter tier at $49/mo and Pro tier at $199/month.</p>
            <table><tr><th>Tier</th><th>Price</th><th>Features</th></tr></table>
        </body></html>
        """
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        ans = entity_content_check.evaluate_page_answerability("pricing", html, dom, "https://example.com/pricing", [])
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertTrue(facts["tier_names"])
        self.assertTrue(facts["price_figures"])
        self.assertTrue(facts["feature_comparison"])
        self.assertEqual(ans["results"][0]["score"], 1.0)

    def test_evaluate_page_answerability_subscription_flow(self):
        """Verify answerability scoring for subscription_flow pages."""
        html = """
        <html><body>
            <h1>Subscribe to Coffee Club</h1>
            <p>Choose your monthly deliveries, frequency, and grind tier.</p>
            <form><select name="frequency"><option>Monthly</option></select><button>Subscribe Now</button></form>
        </body></html>
        """
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        ans = entity_content_check.evaluate_page_answerability("subscription_flow", html, dom, "https://example.com/subscribe", [])
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertTrue(facts["plan_description"])
        self.assertTrue(facts["selection_options"])
        self.assertTrue(facts["cta_action"])
        self.assertEqual(ans["results"][0]["score"], 1.0)

    def test_evaluate_page_answerability_service(self):
        """Verify answerability scoring for service pages."""
        html = """
        <html><body>
            <h1>Enterprise Consulting Services</h1>
            <p>Our capabilities and deliverables include architecture review and SLA guarantees.</p>
            <p>Engagement model: retainer or hourly consulting. Contact sales.</p>
        </body></html>
        """
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        ans = entity_content_check.evaluate_page_answerability("service", html, dom, "https://example.com/service", [])
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertTrue(facts["service_name"])
        self.assertTrue(facts["deliverables"])
        self.assertTrue(facts["engagement_model"])
        self.assertEqual(ans["results"][0]["score"], 1.0)

    def test_evaluate_page_answerability_contact(self):
        """Verify answerability scoring for contact pages."""
        html = """
        <html><body>
            <h1>Contact Us</h1>
            <p>Email: support@example.com | Phone: +1-800-555-0199</p>
            <p>Headquarters: 100 Innovation Way, Suite 400, San Jose, CA.</p>
            <form><button type="submit">Send Message</button></form>
        </body></html>
        """
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        ans = entity_content_check.evaluate_page_answerability("contact", html, dom, "https://example.com/contact", [])
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertTrue(facts["email_channel"])
        self.assertTrue(facts["phone_channel"])
        self.assertTrue(facts["location_or_form"])
        self.assertEqual(ans["results"][0]["score"], 1.0)

    def test_evaluate_page_answerability_empty_product_zero_score(self):
        """Verify an empty Product entity on an empty page scores 0.0 with all facts False."""
        html = "<html><body></body></html>"
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        entities = [{"@type": "Product"}]
        ans = entity_content_check.evaluate_page_answerability("product_detail", html, dom, "https://example.com/p", entities)
        self.assertEqual(ans["status"], "present")
        self.assertEqual(ans["results"][0]["score"], 0.0)
        self.assertFalse(ans["results"][0]["facts"]["product_name"])
        self.assertFalse(ans["results"][0]["facts"]["price"])
        self.assertFalse(ans["results"][0]["facts"]["availability"])
        self.assertFalse(ans["results"][0]["facts"]["specifications"])

    def test_evaluate_page_answerability_contact_no_false_positive(self):
        """Verify '+' symbol and '@' in JSON-LD metadata do NOT falsely trigger contact channels."""
        html = """
        <html><body>
            <p>Our math formula: a + b = c</p>
            <p>No email or phone provided here.</p>
        </body></html>
        """
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        entities = [{"@context": "https://schema.org", "@type": "WebPage"}]
        ans = entity_content_check.evaluate_page_answerability("contact", html, dom, "https://example.com/contact", entities)
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertFalse(facts["email_channel"])
        self.assertFalse(facts["phone_channel"])
        self.assertFalse(facts["location_or_form"])
        self.assertEqual(ans["results"][0]["score"], 0.0)

    def test_evaluate_page_answerability_subscription_no_false_cta(self):
        """Verify arbitrary footer hyperlink does NOT falsely satisfy subscription CTA."""
        html = "<html><body><p>Subscribe club</p><a href=\"/privacy\">Privacy Policy</a></body></html>"
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        ans = entity_content_check.evaluate_page_answerability("subscription_flow", html, dom, "https://example.com/sub", [])
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertTrue(facts["plan_description"])
        self.assertFalse(facts["selection_options"])
        self.assertFalse(facts["cta_action"])
        self.assertEqual(ans["results"][0]["score"], 0.35)

    def test_evaluate_page_answerability_service_no_organization_confusion(self):
        """Verify Organization entity is not falsely credited as a Service name."""
        html = "<html><body><p>Random page content.</p></body></html>"
        dom = entity_content_check.EntityDOMParser()
        dom.feed(html)
        entities = [{"@type": "Organization", "name": "Acme Global"}]
        ans = entity_content_check.evaluate_page_answerability("service", html, dom, "https://example.com/service", entities)
        self.assertEqual(ans["status"], "present")
        facts = ans["results"][0]["facts"]
        self.assertFalse(facts["service_name"])
        self.assertFalse(facts["deliverables"])
        self.assertFalse(facts["engagement_model"])
        self.assertEqual(ans["results"][0]["score"], 0.0)

    def test_check_staging_hostname_in_schema_detects_aem_live(self):
        """E7: Detect non-production staging/preview hostname in Schema.org entity."""
        page = {"url": "https://frescopa.coffee/products/roast"}
        entities = [
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "@id": "https://main--frescopa--hlxsites.aem.live/products/roast#product",
                "name": "House Roast",
                "offers": {
                    "@type": "Offer",
                    "url": "https://main--frescopa--hlxsites.aem.live/products/roast",
                    "price": "18.00",
                },
            }
        ]
        findings = entity_content_check.check_staging_hostname_in_schema(page, entities, "frescopa.coffee")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "E7_STAGING_HOSTNAME_IN_SCHEMA")
        self.assertEqual(findings[0]["cause_id"], "SCHEMA_INTERNAL_CONTRADICTION")

        # Test clean production schema does not trigger finding
        clean_entities = [
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "@id": "https://frescopa.coffee/products/roast#product",
                "name": "House Roast",
                "offers": {
                    "@type": "Offer",
                    "url": "https://frescopa.coffee/products/roast",
                    "price": "18.00",
                },
            }
        ]
        clean_findings = entity_content_check.check_staging_hostname_in_schema(page, clean_entities, "frescopa.coffee")
        self.assertEqual(len(clean_findings), 0)


if __name__ == "__main__":
    unittest.main()
