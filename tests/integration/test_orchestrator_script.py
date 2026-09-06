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


if __name__ == "__main__":
    unittest.main()
