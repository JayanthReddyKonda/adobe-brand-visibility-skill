"""Integration tests for specialist diagnostic sensors cross-module contracts."""

import json
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.helpers.cli_runner import run_skill_script
from tests.helpers.inventory_builder import make_healthy_inventory

ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}


class TestSpecialistContracts(unittest.TestCase):
    """Verifies that all 6 diagnostic specialists conform to standard output contracts."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.gettempdir()
        cls.inv_path = os.path.join(cls.temp_dir, "test_contract_inv.json")
        inv_data = make_healthy_inventory("https://example.com")
        with open(cls.inv_path, "w", encoding="utf-8") as f:
            json.dump(inv_data, f)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.inv_path):
            os.remove(cls.inv_path)

    def _verify_specialist_output(self, skill_name: str, script_file: str, extra_args=None):
        args = [
            "--site",
            "https://example.com",
            "--inventory",
            self.inv_path,
            "--format",
            "json",
        ] + (extra_args or [])

        res = run_skill_script(skill_name, script_file, args)
        self.assertEqual(
            res.returncode,
            0,
            f"{skill_name}/{script_file} returned code {res.returncode}: {res.stderr}",
        )

        data = res.json_safe()
        self.assertIsNotNone(data, f"{skill_name} did not emit valid JSON. Stdout: {res.stdout[:200]}")
        self.assertIn("status", data, f"{skill_name} missing 'status'")
        self.assertEqual(data["status"], "ok")
        self.assertIn("findings", data, f"{skill_name} missing 'findings'")
        self.assertIn("recommendations", data, f"{skill_name} missing 'recommendations'")
        self.assertIsInstance(data["findings"], list)
        self.assertIsInstance(data["recommendations"], list)

        # Validate structure of any emitted findings
        for finding in data["findings"]:
            self.assertIn("id", finding)
            self.assertIn("title", finding)
            self.assertIn("severity", finding)
            self.assertIn(
                finding["severity"],
                ALLOWED_SEVERITIES,
                f"Invalid severity '{finding['severity']}' in {skill_name}",
            )
            self.assertIn("category", finding)
            self.assertIn("root_cause", finding)
            self.assertIn("suggested_action", finding)

    def test_discoverability_audit_contract(self):
        self._verify_specialist_output("discoverability-audit", "discoverability_check.py")

    def test_entity_content_audit_contract(self):
        self._verify_specialist_output("entity-content-audit", "entity_content_check.py")

    def test_fact_consistency_audit_contract(self):
        self._verify_specialist_output("fact-consistency-audit", "fact_consistency_check.py")

    def test_corroboration_authority_audit_contract(self):
        self._verify_specialist_output("corroboration-authority-audit", "corroboration_check.py")

    def test_geo_content_audit_contract(self):
        self._verify_specialist_output("geo-content-audit", "geo_content_check.py")

    def test_engagement_context_audit_contract(self):
        self._verify_specialist_output("engagement-context-audit", "engagement_check.py")


if __name__ == "__main__":
    unittest.main()
