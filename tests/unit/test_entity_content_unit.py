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

    def test_audit_empty_inventory_handled_safely(self):
        """Boundary/Failure test: Empty inventory handled gracefully."""
        inv = make_empty_inventory("https://example.com")
        res = entity_content_check.audit("https://example.com", "example.com", inv)
        self.assertIn("status", res)
        self.assertIsInstance(res.get("findings"), list)


if __name__ == "__main__":
    unittest.main()
