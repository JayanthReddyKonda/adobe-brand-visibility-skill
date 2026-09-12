"""Integration tests for the master orchestrator script."""

import json
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.helpers.cli_runner import run_skill_script, run_validator
from tests.helpers.inventory_builder import (
    make_defective_inventory,
    make_healthy_inventory,
)


class TestOrchestratorScript(unittest.TestCase):
    """Verifies end-to-end functionality of orchestrator.py."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.gettempdir()
        cls.healthy_inv_path = os.path.join(cls.temp_dir, "orch_healthy_inv.json")
        with open(cls.healthy_inv_path, "w", encoding="utf-8") as f:
            json.dump(make_healthy_inventory("https://example.com"), f)

        cls.defective_inv_path = os.path.join(cls.temp_dir, "orch_defective_inv.json")
        with open(cls.defective_inv_path, "w", encoding="utf-8") as f:
            json.dump(make_defective_inventory("https://example.com"), f)

    @classmethod
    def tearDownClass(cls):
        for p in [cls.healthy_inv_path, cls.defective_inv_path]:
            if os.path.exists(p):
                os.remove(p)

    def test_orchestrator_cli_help(self):
        """Verify orchestrator CLI flags."""
        res = run_skill_script("audit-orchestrator", "orchestrator.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--site", res.stdout)
        self.assertIn("--inventory", res.stdout)
        self.assertIn("--output", res.stdout)

    def test_orchestrator_healthy_site_execution(self):
        """Verify orchestrator execution on healthy inventory emits Draft-07 valid JSON."""
        res = run_skill_script(
            "audit-orchestrator",
            "orchestrator.py",
            ["--site", "https://example.com", "--inventory", self.healthy_inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0, f"Orchestrator failed: {res.stderr}")
        report = res.json
        self.assertEqual(report.get("site"), "https://example.com")
        self.assertIn("audited_at", report)
        self.assertIn(report.get("audit_status"), ["complete", "partial"])
        self.assertIn("summary", report)
        self.assertIn("findings", report)
        self.assertIn("proactive_actions", report)

        # Validate with Draft-07 validator
        val_res = run_validator(report)
        self.assertEqual(val_res.returncode, 0, f"Schema validation error: {val_res.stderr}")

    def test_orchestrator_defective_site_execution(self):
        """Verify orchestrator execution on defective inventory detects issues with dual-track fixes."""
        res = run_skill_script(
            "audit-orchestrator",
            "orchestrator.py",
            ["--site", "https://example.com", "--inventory", self.defective_inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0, f"Orchestrator failed: {res.stderr}")
        report = res.json
        findings = report.get("findings", [])
        self.assertGreater(len(findings), 0, "Defective site should yield findings")

        # Verify finding structure conforms to required floor schema
        for f in findings:
            self.assertIn("id", f)
            self.assertIn("title", f)
            self.assertIn("severity", f)
            self.assertIn("evidence", f)
            action = f.get("suggested_action", {})
            self.assertIn("summary", action)
            self.assertIn("priority", action)

        # Validate with Draft-07 validator
        val_res = run_validator(report)
        self.assertEqual(val_res.returncode, 0, f"Schema validation error: {val_res.stderr}")

    def test_orchestrator_telemetry_execution(self):
        """Verify orchestrator --telemetry emits empirical telemetry with causal state."""
        res = run_skill_script(
            "audit-orchestrator",
            "orchestrator.py",
            ["--site", "https://example.com", "--inventory", self.healthy_inv_path, "--telemetry"],
        )
        self.assertEqual(res.returncode, 0, f"Orchestrator --telemetry failed: {res.stderr}")
        telemetry = res.json
        self.assertEqual(telemetry.get("site"), "https://example.com")
        self.assertIn("crawled_at", telemetry)
        self.assertIn("archetype", telemetry)
        self.assertIn("causal_state", telemetry)
        self.assertIn("nodes", telemetry["causal_state"])
        self.assertIn("evidence_index", telemetry)
        self.assertIn("sensor_telemetry", telemetry)

        # Validate with Draft-07 telemetry schema
        schema_file = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "references", "telemetry-schema.json")
        val_res = run_validator(telemetry, schema_path=schema_file)
        self.assertEqual(val_res.returncode, 0, f"Telemetry schema validation error: {val_res.stderr}")

    def test_detect_business_archetype_list_handling(self):
        """Verify archetype detection correctly handles list-wrapped title and h1 fields."""
        orch_dir = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "scripts")
        if orch_dir not in sys.path:
            sys.path.insert(0, orch_dir)
        import orchestrator  # type: ignore

        list_inv = {
            "site": "https://store.example.com",
            "pages": [
                {
                    "url": "https://store.example.com/items/shoe",
                    "title": ["Acme Running Shoes - Add to Cart"],
                    "h1": ["Acme High Performance Running Shoes"],
                    "page_type": "product",
                    "clean_text": "Buy now, add to cart, $99 sku-12345 in stock",
                }
            ],
        }
        arch = orchestrator.detect_business_archetype(list_inv)
        self.assertEqual(arch, "ecommerce")

    def test_causal_suppression_unscoped_finding_no_leak(self):
        """Verify that an isolated Layer 0 finding on one route does not suppress downstream findings on other routes."""
        orch_dir = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "scripts")
        if orch_dir not in sys.path:
            sys.path.insert(0, orch_dir)
        import orchestrator  # type: ignore

        base = "https://example.com"
        domain = "example.com"
        inv = {
            "site": base,
            "pages": [
                {"url": f"{base}/", "status": 200, "word_count": 500, "snr": 0.6, "page_type": "homepage"},
                {"url": f"{base}/pricing", "status": 200, "word_count": 400, "snr": 0.5, "page_type": "pricing"},
            ],
        }
        specialist_results = {
            "discoverability-audit": {
                "findings": [
                    {
                        "id": "F-001",
                        "cause_id": "META_DIRECTIVE_CONFLICT",
                        "severity": "high",
                        "scope": f"{base}/blocked-route",
                        "url": f"{base}/blocked-route",
                        "title": "Blocked route",
                        "root_cause": "Blocked",
                        "evidence": "noindex on blocked-route",
                        "suggested_action": {"summary": "Fix noindex", "technical_fix": "Fix", "creative_fix": "Fix", "priority": "high"},
                    }
                ]
            },
            "fact-consistency-audit": {
                "findings": [
                    {
                        "id": "F-002",
                        "cause_id": "FIRST_PARTY_FACT_CONFLICT",
                        "severity": "medium",
                        "scope": f"{base}/pricing",
                        "url": f"{base}/pricing",
                        "title": "Price conflict",
                        "root_cause": "Conflict on pricing",
                        "evidence": "Price is $10 vs $20",
                        "suggested_action": {"summary": "Align price", "technical_fix": "Fix", "creative_fix": "Fix", "priority": "medium"},
                    }
                ]
            },
        }
        report = orchestrator.synthesize_audit_report(base, inv, specialist_results)
        findings = report.get("findings", [])
        cids = [f.get("cause_id") or f.get("id") for f in findings]
        self.assertIn("FIRST_PARTY_FACT_CONFLICT", cids)


if __name__ == "__main__":
    unittest.main()


