"""Unit tests for Fact Consistency & Lifecycle Audit sensor."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "fact-consistency-audit", "scripts")
for p in [PROJECT_ROOT, SKILL_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import fact_consistency_check

from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_empty_inventory,
    make_healthy_inventory,
)


class TestFactConsistencyUnit(unittest.TestCase):
    """Verifies cross-page fact extraction, multi-currency parsing, and contradiction detection."""

    def test_extract_currency_handling(self):
        """Unit test: Currency extraction across symbols, codes, and None."""
        self.assertEqual(fact_consistency_check.extract_currency("$49.00"), "USD")
        self.assertEqual(fact_consistency_check.extract_currency("USD 100"), "USD")
        self.assertEqual(fact_consistency_check.extract_currency("€1.499,00"), "EUR")
        self.assertEqual(fact_consistency_check.extract_currency("49,99 EUR"), "EUR")
        self.assertEqual(fact_consistency_check.extract_currency("£25.50"), "GBP")
        self.assertEqual(fact_consistency_check.extract_currency("GBP 500"), "GBP")
        self.assertEqual(fact_consistency_check.extract_currency("₹4,999"), "INR")
        self.assertEqual(fact_consistency_check.extract_currency("Rs. 1500"), "INR")
        self.assertEqual(fact_consistency_check.extract_currency("INR 2500"), "INR")
        self.assertEqual(fact_consistency_check.extract_currency("¥15,000"), "JPY")
        self.assertEqual(fact_consistency_check.extract_currency("R$ 199,00"), "BRL")
        self.assertEqual(fact_consistency_check.extract_currency("AED 350"), "AED")
        self.assertEqual(fact_consistency_check.extract_currency("CAD 89.00"), "CAD")
        self.assertEqual(fact_consistency_check.extract_currency("AUD 120.00"), "AUD")
        self.assertEqual(fact_consistency_check.extract_currency(None), "UNKNOWN")
        self.assertEqual(fact_consistency_check.extract_currency(""), "UNKNOWN")

    def test_extract_interval(self):
        """Unit test: Extracts billing intervals."""
        self.assertEqual(fact_consistency_check.extract_interval("Starting at $49/mo"), "month")
        self.assertEqual(fact_consistency_check.extract_interval("$99 per month"), "month")
        self.assertEqual(fact_consistency_check.extract_interval("$15 per user/mo"), "month")
        self.assertEqual(fact_consistency_check.extract_interval("$499/yr"), "year")
        self.assertEqual(fact_consistency_check.extract_interval("Billed annually at $399"), "year")
        self.assertEqual(fact_consistency_check.extract_interval("$25/wk"), "week")
        self.assertEqual(fact_consistency_check.extract_interval("$5 per day"), "day")
        self.assertEqual(fact_consistency_check.extract_interval("One-time payment of $299"), "one_time")

    def test_normalize_price_str(self):
        """Unit test: Normalizes US, European, and integer price formats."""
        self.assertEqual(fact_consistency_check.normalize_price_str("$49.99"), "49.99")
        self.assertEqual(fact_consistency_check.normalize_price_str("1,250.50"), "1250.50")
        self.assertEqual(fact_consistency_check.normalize_price_str("1.499,00"), "1499.00")
        self.assertEqual(fact_consistency_check.normalize_price_str("49,99"), "49.99")
        self.assertEqual(fact_consistency_check.normalize_price_str("₹5,499"), "5499.00")
        self.assertEqual(fact_consistency_check.normalize_price_str("100"), "100.00")
        self.assertIsNone(fact_consistency_check.normalize_price_str(None))

    def test_audit_consistent_site(self):
        """Success test: Site with consistent pricing passes without contradiction findings."""
        inv = make_healthy_inventory("https://example.com")
        res = fact_consistency_check.audit("https://example.com", "example.com", inv)
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertNotIn("FIRST_PARTY_FACT_CONFLICT", cause_ids)

    def test_audit_conflicting_prices_flags_defect(self):
        """Failure test: Site with conflicting prices flags FIRST_PARTY_FACT_CONFLICT."""
        inv = make_defective_inventory("https://example.com")
        res = fact_consistency_check.audit("https://example.com", "example.com", inv)
        self.assertEqual(res["status"], "ok")
        findings = res.get("findings", [])
        cause_ids = [f.get("cause_id") for f in findings if isinstance(f, dict)]
        self.assertIn("FIRST_PARTY_FACT_CONFLICT", cause_ids)

    def test_audit_empty_inventory(self):
        """Boundary/Failure test: Empty inventory handled without crashing."""
        inv = make_empty_inventory("https://example.com")
        res = fact_consistency_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIsInstance(res.get("findings"), list)

    def test_schema_recurring_interval_extraction(self):
        """Elevation test: Schema.org offers with unitCode MON extract interval as month."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Cloud Pro SaaS",
                    "offers": {
                        "@type": "Offer",
                        "price": "99.00",
                        "priceCurrency": "USD",
                        "priceSpecification": {
                            "@type": "UnitPriceSpecification",
                            "price": "99.00",
                            "priceCurrency": "USD",
                            "unitCode": "MON"
                        }
                    }
                }
                </script>
            </head>
            <body><h1>Cloud Pro SaaS</h1></body>
        </html>
        """
        facts = fact_consistency_check.extract_scoped_facts(html, "https://example.com/pricing")
        scoped_prices = facts.get("scoped_prices", [])
        self.assertEqual(len(scoped_prices), 1)
        self.assertEqual(scoped_prices[0]["interval"], "month")
        self.assertEqual(scoped_prices[0]["currency"], "USD")
        self.assertEqual(scoped_prices[0]["price"], "99.00")


if __name__ == "__main__":
    unittest.main()
