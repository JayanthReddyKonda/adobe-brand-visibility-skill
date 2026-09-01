import unittest
import json
import subprocess
import os
import tempfile

class TestStateAndOrchestration(unittest.TestCase):
    def setUp(self):
        self.orch_script = "brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py"
        self.val_script = "brand-ai-readiness-audit/skills/audit-orchestrator/scripts/validate_report.py"

    def test_orchestrator_on_synthetic_inventory(self):
        inv_data = {
            "site": "https://testbrand.com",
            "pages": [{"url": "https://testbrand.com/", "status": 200, "content_type": "text/html", "page_type": "homepage", "html": "<html><head><title>Test</title></head><body><h1>Test</h1><p>Test offers plans starting at $49/mo because algorithms improve speed by 30%.</p></body></html>"}],
            "robots_txt": "User-agent: *\nAllow: /\n",
            "sitemaps": []
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(inv_data, tf)
            tf_path = tf.name
            
        try:
            res = subprocess.run(["python3", self.orch_script, "--site", "https://testbrand.com", "--inventory", tf_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            report = json.loads(res.stdout)
            self.assertEqual(report["audit_status"], "complete")
            self.assertIn("summary", report)
            self.assertIn("findings", report)
            self.assertIn("proactive_actions", report)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_schema_validator_rejects_missing_fields(self):
        bad_report = {"site": "https://example.com"}  # Missing summary, findings, audited_at
        val_res = subprocess.run(["python3", self.val_script, "-"], input=json.dumps(bad_report), capture_output=True, text=True)
        self.assertNotEqual(val_res.returncode, 0)

    def test_schema_validator_accepts_valid_dual_track_actions(self):
        valid_report = {
            "site": "https://example.com",
            "audited_at": "2026-09-01T12:00:00Z",
            "audit_status": "complete",
            "summary": {"total_findings": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "findings": [],
            "proactive_actions": [
                {
                    "id": "action-1",
                    "title": "Add Organization Schema",
                    "category": "entity-identity",
                    "summary": "Publish machine-explicit schema",
                    "technical_fix": "Add JSON-LD block",
                    "creative_fix": "Standardize hero heading",
                    "priority": "medium",
                    "verification": "Inspect homepage JSON-LD"
                }
            ]
        }
        val_res = subprocess.run(["python3", self.val_script, "-"], input=json.dumps(valid_report), capture_output=True, text=True)
        self.assertEqual(val_res.returncode, 0)

    def test_severity_count_consistency(self):
        report = {
            "site": "https://example.com",
            "audited_at": "2026-09-01T12:00:00Z",
            "audit_status": "complete",
            "summary": {"total_findings": 2, "critical": 1, "high": 1, "medium": 0, "low": 0},
            "findings": [
                {
                    "id": "f1",
                    "title": "Critical Defect",
                    "severity": "critical",
                    "category": "discoverability",
                    "root_cause": "Blocked",
                    "evidence": {"summary": "Blocked", "scope": "global", "sources": [{"url": "https://example.com", "type": "page", "observation": "Blocked"}]},
                    "suggested_action": {"summary": "Fix", "priority": "critical", "technical_fix": "Fix", "creative_fix": None, "verification": "Verify"}
                },
                {
                    "id": "f2",
                    "title": "High Defect",
                    "severity": "high",
                    "category": "discoverability",
                    "root_cause": "Blocked",
                    "evidence": {"summary": "Blocked", "scope": "global", "sources": [{"url": "https://example.com", "type": "page", "observation": "Blocked"}]},
                    "suggested_action": {"summary": "Fix", "priority": "high", "technical_fix": "Fix", "creative_fix": None, "verification": "Verify"}
                }
            ],
            "proactive_actions": []
        }
        val_res = subprocess.run(["python3", self.val_script, "-"], input=json.dumps(report), capture_output=True, text=True)
        self.assertEqual(val_res.returncode, 0)

    def test_empty_site_handling(self):
        # Empty pages list should yield status incomplete/partial without crash
        inv_data = {"site": "https://emptybrand.com", "pages": [], "robots_txt": "", "sitemaps": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(inv_data, tf)
            tf_path = tf.name
        try:
            res = subprocess.run(["python3", self.orch_script, "--site", "https://emptybrand.com", "--inventory", tf_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

if __name__ == "__main__":
    unittest.main()
