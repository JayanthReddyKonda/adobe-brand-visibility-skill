"""Integration tests for cross-module contract failures and failure-state handling."""

import json
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.helpers.cli_runner import run_skill_script, run_validator
from tests.helpers.inventory_builder import make_empty_inventory


class TestPartialFailureSemantics(unittest.TestCase):
    """Verifies graceful recovery and failure-state propagation across module boundaries."""

    def setUp(self):
        self.temp_dir = tempfile.gettempdir()
        self.corrupt_inv_path = os.path.join(self.temp_dir, "corrupt_inv.json")
        with open(self.corrupt_inv_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json content ...")

        self.empty_pages_inv_path = os.path.join(self.temp_dir, "empty_pages_inv.json")
        with open(self.empty_pages_inv_path, "w", encoding="utf-8") as f:
            json.dump(make_empty_inventory("https://example.com"), f)

        self.malformed_page_inv_path = os.path.join(self.temp_dir, "malformed_page_inv.json")
        with open(self.malformed_page_inv_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "site": "https://example.com",
                    "pages": [
                        # Missing 'url' and 'html' is None
                        {"status": 500, "content_type": None, "html": None},
                        # Non-dict item
                        "just a string instead of dict",
                    ],
                },
                f,
            )

    def tearDown(self):
        for p in [self.corrupt_inv_path, self.empty_pages_inv_path, self.malformed_page_inv_path]:
            if os.path.exists(p):
                os.remove(p)

    def test_specialists_handle_corrupt_inventory_safely(self):
        """Failure test: Corrupt inventory JSON does not cause unhandled tracebacks in specialists."""
        specialists = [
            ("discoverability-audit", "discoverability_check.py"),
            ("entity-content-audit", "entity_content_check.py"),
            ("fact-consistency-audit", "fact_consistency_check.py"),
            ("corroboration-authority-audit", "corroboration_check.py"),
            ("geo-content-audit", "geo_content_check.py"),
            ("engagement-context-audit", "engagement_check.py"),
        ]
        for sname, sfile in specialists:
            res = run_skill_script(
                sname,
                sfile,
                ["--site", "https://example.com", "--inventory", self.corrupt_inv_path],
            )
            # Must exit gracefully without uncaught Python exception traceback
            self.assertNotIn("Traceback (most recent call last):", res.stderr)

    def test_specialists_handle_nonexistent_inventory_path(self):
        """Failure test: Non-existent inventory path handled cleanly without crashing."""
        res = run_skill_script(
            "discoverability-audit",
            "discoverability_check.py",
            ["--site", "https://example.com", "--inventory", "/nonexistent/path/inv.json"],
        )
        self.assertNotIn("Traceback (most recent call last):", res.stderr)

    def test_specialists_handle_empty_pages_inventory(self):
        """Boundary/Inconclusive test: Zero crawled pages does not cause ZeroDivisionError or IndexError."""
        specialists = [
            ("discoverability-audit", "discoverability_check.py"),
            ("entity-content-audit", "entity_content_check.py"),
            ("fact-consistency-audit", "fact_consistency_check.py"),
            ("corroboration-authority-audit", "corroboration_check.py"),
            ("geo-content-audit", "geo_content_check.py"),
            ("engagement-context-audit", "engagement_check.py"),
        ]
        for sname, sfile in specialists:
            res = run_skill_script(
                sname,
                sfile,
                ["--site", "https://example.com", "--inventory", self.empty_pages_inv_path],
            )
            self.assertEqual(res.returncode, 0, f"{sname} failed on empty pages: {res.stderr}")
            data = res.json_safe()
            self.assertIsNotNone(data, f"{sname} failed to return valid JSON")
            self.assertIn("status", data)

    def test_inconclusive_audit_report_validates_in_schema(self):
        """Inconclusive state test: Inconclusive audit reports strictly validate under Draft-07 schema."""
        inconclusive_report = {
            "site": "https://offline-example.com",
            "audited_at": "2026-09-06T12:00:00Z",
            "audit_status": "failed",
            "summary": {
                "total_findings": 1,
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "findings": [
                {
                    "id": "finding-net-unreachable",
                    "title": "Target domain unreachable during audit acquisition",
                    "severity": "critical",
                    "confidence": "high",
                    "category": "discoverability",
                    "root_cause": "DNS resolution failure or server timeout",
                    "evidence": "Socket timeout connecting to https://offline-example.com",
                    "suggested_action": {
                        "summary": "Verify web server availability and firewall rules",
                        "priority": "critical",
                        "technical_fix": "Ensure DNS records are active and port 443 is open",
                        "creative_fix": None,
                        "verification": "Verify reachability with curl -I https://offline-example.com",
                    },
                }
            ],
            "proactive_actions": [],
        }
        res = run_validator(inconclusive_report)
        self.assertEqual(res.returncode, 0, f"Inconclusive report failed schema gate: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
