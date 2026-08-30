import unittest
import subprocess
import os
import json

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.orchestrator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py"))
        self.validator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../brand-ai-readiness-audit/skills/audit-orchestrator/scripts/validate_report.py"))

    def test_example_com_audit(self):
        # Run orchestrator against example.com
        result = subprocess.run(["python3", self.orchestrator_path, "--site", "example.com"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Parse JSON
        report = json.loads(result.stdout)
        self.assertEqual(report["site"], "https://example.com")
        self.assertIn("audit_status", report)
        self.assertTrue(report["audit_status"] in ["complete", "partial", "failed"])
        
        # Run validator
        val_result = subprocess.run(["python3", self.validator_path, "-"], input=result.stdout, capture_output=True, text=True)
        self.assertEqual(val_result.returncode, 0, f"Validator failed: {val_result.stderr}")

if __name__ == '__main__':
    unittest.main()
