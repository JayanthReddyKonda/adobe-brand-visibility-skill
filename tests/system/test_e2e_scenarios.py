"""System end-to-end tests simulating complete audit lifecycles across realistic scenarios."""

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


class TestE2EScenarios(unittest.TestCase):
    """Verifies end-to-end audit simulations from inventory acquisition through schema validation."""

    def setUp(self):
        self.temp_dir = tempfile.gettempdir()
        self.healthy_inv_path = os.path.join(self.temp_dir, "e2e_healthy_inv.json")
        with open(self.healthy_inv_path, "w", encoding="utf-8") as f:
            json.dump(make_healthy_inventory("https://example.com"), f)

        self.defective_inv_path = os.path.join(self.temp_dir, "e2e_defective_inv.json")
        with open(self.defective_inv_path, "w", encoding="utf-8") as f:
            json.dump(make_defective_inventory("https://example.com"), f)

    def tearDown(self):
        for p in [self.healthy_inv_path, self.defective_inv_path]:
            if os.path.exists(p):
                os.remove(p)

    def test_e2e_healthy_site_simulation(self):
        """E2E Scenario 1: Healthy enterprise website lifecycle."""
        # 1. Fan out across all 6 diagnostic specialists
        specialists = [
            ("discoverability-audit", "discoverability_check.py"),
            ("entity-content-audit", "entity_content_check.py"),
            ("fact-consistency-audit", "fact_consistency_check.py"),
            ("corroboration-authority-audit", "corroboration_check.py"),
            ("geo-content-audit", "geo_content_check.py"),
            ("engagement-context-audit", "engagement_check.py"),
        ]
        all_findings = []
        for sname, sfile in specialists:
            res = run_skill_script(
                sname,
                sfile,
                ["--site", "https://example.com", "--inventory", self.healthy_inv_path, "--format", "json"],
            )
            self.assertEqual(res.returncode, 0)
            data = res.json
            all_findings.extend(data.get("findings", []))

        # 2. Synthesize complete final report
        critical_count = sum(1 for f in all_findings if f.get("severity") == "critical")
        high_count = sum(1 for f in all_findings if f.get("severity") == "high")
        medium_count = sum(1 for f in all_findings if f.get("severity") == "medium")
        low_count = sum(1 for f in all_findings if f.get("severity") == "low")

        final_report = {
            "site": "https://example.com",
            "audited_at": "2026-09-06T12:00:00Z",
            "audit_status": "complete",
            "summary": {
                "total_findings": len(all_findings),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
            },
            "findings": all_findings,
            "proactive_actions": [
                {
                    "id": "proactive-1",
                    "title": "Maintain structured llms.txt manifest",
                    "summary": "Deploy and maintain an llms.txt manifest to guide AI retrieval engines.",
                    "priority": "low",
                    "technical_fix": "Deploy /llms.txt with modular documentation links",
                    "creative_fix": "Keep executive summaries clear and concise",
                    "verification": "HTTP 200 on /llms.txt",
                }
            ],
        }

        # 3. Pass through Draft-07 schema gate
        val_res = run_validator(final_report)
        self.assertEqual(val_res.returncode, 0, f"Schema validation failed: {val_res.stderr}")
        self.assertEqual(critical_count, 0, "Healthy site should have 0 critical defects")

    def test_e2e_defective_site_simulation(self):
        """E2E Scenario 2: Defective website triggering hard failures and dual-track remediation."""
        specialists = [
            ("discoverability-audit", "discoverability_check.py"),
            ("entity-content-audit", "entity_content_check.py"),
            ("fact-consistency-audit", "fact_consistency_check.py"),
            ("corroboration-authority-audit", "corroboration_check.py"),
            ("geo-content-audit", "geo_content_check.py"),
            ("engagement-context-audit", "engagement_check.py"),
        ]
        all_findings = []
        for sname, sfile in specialists:
            res = run_skill_script(
                sname,
                sfile,
                ["--site", "https://example.com", "--inventory", self.defective_inv_path, "--format", "json"],
            )
            self.assertEqual(res.returncode, 0)
            data = res.json
            all_findings.extend(data.get("findings", []))

        # Ensure hard failure modes were detected
        cause_ids = {f.get("cause_id") for f in all_findings if f.get("cause_id")}
        self.assertTrue(
            any("BLOCKED" in c or "NOINDEX" in c or "AMBIGUITY" in c or "CONFLICT" in c for c in cause_ids),
            f"Expected hard failure causes in {cause_ids}",
        )

        # Synthesize final report with dual-track remediation
        final_report = {
            "site": "https://example.com",
            "audited_at": "2026-09-06T12:00:00Z",
            "audit_status": "complete",
            "summary": {
                "total_findings": len(all_findings),
                "critical": sum(1 for f in all_findings if f.get("severity") == "critical"),
                "high": sum(1 for f in all_findings if f.get("severity") == "high"),
                "medium": sum(1 for f in all_findings if f.get("severity") == "medium"),
                "low": sum(1 for f in all_findings if f.get("severity") == "low"),
            },
            "findings": all_findings,
            "proactive_actions": [],
        }

        # Validate through Draft-07 schema gate
        val_res = run_validator(final_report)
        self.assertEqual(val_res.returncode, 0, f"Schema validation failed: {val_res.stderr}")


if __name__ == "__main__":
    unittest.main()
