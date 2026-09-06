"""Unit tests for Schema.org JSON-LD extraction, graph flattening, and syntax error resilience."""

import json
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "src", "skills", "web-scraper", "scripts")
if SCRAPER_DIR not in sys.path:
    sys.path.insert(0, SCRAPER_DIR)

from crawler.jsonld import JsonLdExtractor

from tests.fixtures.jsonld_fixtures import (
    MALFORMED_JSONLD_RAW,
    VALID_GRAPH_JSONLD,
    VALID_ORGANIZATION_JSONLD,
    VALID_PRODUCT_WITH_OFFER_JSONLD,
)


class TestEvidenceAndJsonLd(unittest.TestCase):
    """Verifies structured data extraction from JSON-LD blocks."""

    def test_single_organization_extraction(self):
        """Success test: Valid Organization block parsed cleanly."""
        blocks = [(json.dumps(VALID_ORGANIZATION_JSONLD), "head", 0)]
        schemas, facts, observations = JsonLdExtractor.parse_blocks(blocks, "https://example.com/")
        self.assertEqual(len(schemas), 1)
        self.assertEqual(schemas[0]["@type"], "Organization")
        self.assertEqual(schemas[0]["name"], "Enterprise AI Cloud")
        self.assertEqual(len(schemas[0]["sameAs"]), 3)

    def test_product_with_offers_fact_extraction(self):
        """Success test: Product with Offer extracts price and currency fact candidates."""
        blocks = [(json.dumps(VALID_PRODUCT_WITH_OFFER_JSONLD), "head", 0)]
        schemas, facts, observations = JsonLdExtractor.parse_blocks(blocks, "https://example.com/pricing")
        self.assertEqual(len(schemas), 1)
        self.assertEqual(schemas[0]["@type"], "Product")
        # Verify fact candidate locator
        price_facts = [f for f in facts if f.attribute == "price"]
        self.assertTrue(len(price_facts) >= 1)
        self.assertEqual(float(price_facts[0].value), 49.0)

    def test_graph_flattening(self):
        """Success test: @graph structure flattens into individual top-level entities."""
        blocks = [(json.dumps(VALID_GRAPH_JSONLD), "head", 0)]
        schemas, facts, observations = JsonLdExtractor.parse_blocks(blocks, "https://example.com/")
        types = [s.get("@type") for s in schemas]
        self.assertIn("Organization", types)
        self.assertIn("Product", types)

    def test_malformed_jsonld_syntax_error_resilience(self):
        """Failure/Resilience test: Malformed JSON-LD does not crash, logs schema_syntax_error."""
        blocks = [(MALFORMED_JSONLD_RAW, "head", 0)]
        schemas, facts, observations = JsonLdExtractor.parse_blocks(blocks, "https://example.com/broken")
        self.assertEqual(len(schemas), 0)
        error_obs = [o for o in observations if o.type == "schema_syntax_error"]
        self.assertEqual(len(error_obs), 1)
        self.assertEqual(error_obs[0].value, "jsonld_parse_failure")

    def test_empty_jsonld_blocks(self):
        """Boundary test: Empty raw blocks records schema_gap observation."""
        schemas, facts, observations = JsonLdExtractor.parse_blocks([], "https://example.com/empty")
        self.assertEqual(len(schemas), 0)
        gap_obs = [o for o in observations if o.type == "schema_gap"]
        self.assertEqual(len(gap_obs), 1)


if __name__ == "__main__":
    unittest.main()
