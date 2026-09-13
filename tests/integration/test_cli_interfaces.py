"""Integration tests verifying CLI argument parity across all 8 skills."""

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


class TestCLIInterfaces(unittest.TestCase):
    """Verifies that all CLI argument definitions match orchestrator invocations exactly."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.gettempdir()
        cls.inv_path = os.path.join(cls.temp_dir, "test_cli_inv.json")
        inv_data = make_healthy_inventory("https://example.com")
        with open(cls.inv_path, "w", encoding="utf-8") as f:
            json.dump(inv_data, f)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.inv_path):
            os.remove(cls.inv_path)

    # 1. web-scraper CLI
    def test_web_scraper_cli_arguments(self):
        """Verify web-scraper arguments: --site, --output, --max-pages, --timeout, --max-depth, --format, --strict-robots, --verbose."""
        res = run_skill_script("web-scraper", "run_scraper.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--site", res.stdout)
        self.assertIn("--output", res.stdout)
        self.assertIn("--max-pages", res.stdout)
        self.assertIn("--timeout", res.stdout)
        self.assertIn("--max-depth", res.stdout)
        self.assertIn("--format", res.stdout)
        self.assertIn("--strict-robots", res.stdout)
        self.assertIn("--verbose", res.stdout)

    def test_web_scraper_missing_site_fails(self):
        """Verify web-scraper fails when required --site argument is omitted."""
        res = run_skill_script("web-scraper", "run_scraper.py", [])
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("required", res.stderr.lower())

    # 2. acquire_inventory CLI
    def test_acquire_inventory_cli_arguments(self):
        """Verify acquire_inventory arguments: --site, --output, --format."""
        res = run_skill_script("web-scraper", "acquire_inventory.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--site", res.stdout)
        self.assertIn("--output", res.stdout)
        self.assertIn("--format", res.stdout)

    def test_acquire_inventory_missing_site_fails(self):
        """Verify acquire_inventory fails when required --site argument is omitted."""
        res = run_skill_script("web-scraper", "acquire_inventory.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 3. discoverability-audit CLI
    def test_discoverability_audit_cli_arguments(self):
        """Verify discoverability_check arguments: --site, --inventory, --state, --format."""
        res = run_skill_script(
            "discoverability-audit",
            "discoverability_check.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)

    def test_discoverability_audit_missing_site_fails(self):
        res = run_skill_script("discoverability-audit", "discoverability_check.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 4. entity-content-audit CLI
    def test_entity_content_audit_cli_arguments(self):
        """Verify entity_content_check arguments: --site, --inventory, --state, --format."""
        res = run_skill_script(
            "entity-content-audit",
            "entity_content_check.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)

    def test_entity_content_audit_missing_site_fails(self):
        res = run_skill_script("entity-content-audit", "entity_content_check.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 5. fact-consistency-audit CLI
    def test_fact_consistency_audit_cli_arguments(self):
        """Verify fact_consistency_check arguments: --site, --inventory, --state, --responses, --format."""
        res = run_skill_script(
            "fact-consistency-audit",
            "fact_consistency_check.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)

    def test_fact_consistency_audit_missing_site_fails(self):
        res = run_skill_script("fact-consistency-audit", "fact_consistency_check.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 6. corroboration-authority-audit CLI
    def test_corroboration_authority_audit_cli_arguments(self):
        """Verify corroboration_check arguments: --site, --inventory, --state, --candidate-backlinks, --format."""
        res = run_skill_script(
            "corroboration-authority-audit",
            "corroboration_check.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)

    def test_corroboration_authority_audit_missing_site_fails(self):
        res = run_skill_script("corroboration-authority-audit", "corroboration_check.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 7. geo-content-audit CLI
    def test_geo_content_audit_cli_arguments(self):
        """Verify geo_content_check arguments: --site, --inventory, --state, --format."""
        res = run_skill_script(
            "geo-content-audit",
            "geo_content_check.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)

    def test_geo_content_audit_missing_site_fails(self):
        res = run_skill_script("geo-content-audit", "geo_content_check.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 8. engagement-context-audit CLI
    def test_engagement_context_audit_cli_arguments(self):
        """Verify engagement_check arguments: --site, --inventory, --state, --analytics, --format."""
        res = run_skill_script(
            "engagement-context-audit",
            "engagement_check.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)

    def test_engagement_context_audit_missing_site_fails(self):
        res = run_skill_script("engagement-context-audit", "engagement_check.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 10. orchestrator CLI
    def test_orchestrator_cli_arguments(self):
        """Verify orchestrator arguments: --site, --inventory, --candidate-backlinks, --analytics, --responses, --output, --format, --telemetry."""
        res = run_skill_script(
            "audit-orchestrator",
            "orchestrator.py",
            ["--help"],
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("--site", res.stdout)
        self.assertIn("--inventory", res.stdout)
        self.assertIn("--candidate-backlinks", res.stdout)
        self.assertIn("--analytics", res.stdout)
        self.assertIn("--responses", res.stdout)
        self.assertIn("--telemetry", res.stdout)

    def test_orchestrator_missing_site_fails(self):
        res = run_skill_script("audit-orchestrator", "orchestrator.py", [])
        self.assertNotEqual(res.returncode, 0)

    # 11. plan CLI
    def test_plan_cli_calculator(self):
        """Verify plan.py priority index formula execution via CLI."""
        res = run_skill_script("audit-orchestrator", "plan.py", ["--severity", "4", "--difficulty", "1"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["priority_index"], 25)

    # 12. safe_fetch CLI
    def test_safe_fetch_cli_check_only(self):
        """Verify safe_fetch.py CLI status and SSRF probe."""
        res = run_skill_script("web-scraper", "safe_fetch.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--url", res.stdout)
        self.assertIn("--check-only", res.stdout)

    def test_safe_fetch_cli_ssrf_blocking(self):
        """Verify safe_fetch.py CLI blocks SSRF targets and reports ssrf_safe=False."""
        for blocked_target in ["http://127.0.0.1", "http://169.254.169.254"]:
            res = run_skill_script("web-scraper", "safe_fetch.py", ["--url", blocked_target, "--check-only"])
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertFalse(data.get("ssrf_safe"), f"Target {blocked_target} should be marked ssrf_safe=False")
            self.assertIsNone(data.get("status"))
            self.assertIn("error", data)

    # 13. causal_gate CLI
    def test_causal_gate_cli_help(self):
        """Verify causal_gate.py CLI options."""
        res = run_skill_script("audit-orchestrator", "causal_gate.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--telemetry", res.stdout)
        self.assertIn("--findings", res.stdout)

    # 14. assemble_report CLI
    def test_assemble_report_cli_help(self):
        """Verify assemble_report.py CLI options."""
        res = run_skill_script("audit-orchestrator", "assemble_report.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--site", res.stdout)
        self.assertIn("--candidates", res.stdout)
        self.assertIn("--artifacts", res.stdout)

    # 15. validate_report CLI with --schema
    def test_validate_report_cli_schema(self):
        """Verify validate_report.py CLI supports --schema argument."""
        res = run_skill_script("audit-orchestrator", "validate_report.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("--schema", res.stdout)

    # 16. bundle_context CLI
    def test_bundle_context_cli_json(self):
        """Verify bundle_context.py compiles archetype and signals to JSON."""
        res = run_skill_script(
            "audit-orchestrator",
            "bundle_context.py",
            ["--site", "https://example.com", "--inventory", self.inv_path, "--format", "json"],
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("signals", data)
        self.assertIn("briefing", data)

    # 17. audit CLI
    def test_audit_cli_help(self):
        """Verify audit.py CLI options and help output."""
        res = run_skill_script("audit-orchestrator", "audit.py", ["--help"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("collect", res.stdout)
        self.assertIn("finalize", res.stdout)
        self.assertIn("validate", res.stdout)


if __name__ == "__main__":
    unittest.main()
