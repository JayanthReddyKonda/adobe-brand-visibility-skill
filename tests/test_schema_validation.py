import json
import subprocess
import unittest


class TestSchemaValidationGate(unittest.TestCase):
    def setUp(self):
        self.val_script = "src/skills/audit-orchestrator/scripts/validate_report.py"

    def test_valid_report_passes(self):
        valid_report = {
            "site": "https://example.com",
            "audited_at": "2026-09-01T12:00:00Z",
            "audit_status": "complete",
            "summary": {"total_findings": 1, "critical": 0, "high": 1, "medium": 0, "low": 0},
            "findings": [
                {
                    "id": "finding-1",
                    "title": "Robots.txt blocks AI SearchBot",
                    "severity": "high",
                    "category": "discoverability",
                    "root_cause": "User-agent Disallow directive",
                    "evidence": {
                        "summary": "Disallow / found",
                        "scope": "robots.txt",
                        "sources": [
                            {
                                "url": "https://example.com/robots.txt",
                                "type": "robots_txt",
                                "observation": "Disallow: /",
                            }
                        ],
                    },
                    "suggested_action": {
                        "summary": "Allow AI bots",
                        "priority": "high",
                        "technical_fix": "Add Allow: /",
                        "creative_fix": None,
                        "verification": "Curl robots.txt",
                    },
                }
            ],
            "proactive_actions": [],
        }
        res = subprocess.run(
            ["python3", self.val_script, "-"],
            input=json.dumps(valid_report),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

    def test_invalid_severity_fails(self):
        invalid_report = {
            "site": "https://example.com",
            "audited_at": "2026-09-01T12:00:00Z",
            "audit_status": "complete",
            "summary": {"total_findings": 1, "critical": 0, "high": 1, "medium": 0, "low": 0},
            "findings": [
                {
                    "id": "finding-1",
                    "title": "Invalid Severity Finding",
                    "severity": "info",  # 'info' is forbidden by schema
                    "category": "discoverability",
                    "root_cause": "Test",
                    "evidence": {
                        "summary": "Test",
                        "scope": "global",
                        "sources": [{"url": "https://example.com", "type": "page", "observation": "Test"}],
                    },
                    "suggested_action": {
                        "summary": "Test",
                        "priority": "low",
                        "technical_fix": "Fix",
                        "creative_fix": None,
                        "verification": "Verify",
                    },
                }
            ],
            "proactive_actions": [],
        }
        res = subprocess.run(
            ["python3", self.val_script, "-"],
            input=json.dumps(invalid_report),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res.returncode, 0)

    def test_string_evidence_passes(self):
        # Conformance with sample report in round3_PS.pdf page 2
        report_with_string_evidence = {
            "site": "example.com",
            "audited_at": "2026-09-20T14:32:00Z",
            "summary": {
                "total_findings": 1,
                "critical": 0,
                "high": 1,
                "medium": 0,
            },
            "findings": [
                {
                    "id": "F-001",
                    "title": "No JSON-LD structured data on product pages",
                    "severity": "high",
                    "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
                    "suggested_action": {
                        "summary": "Add Product/Offer JSON-LD to every product page.",
                        "priority": "high",
                    },
                }
            ],
        }
        res = subprocess.run(
            ["python3", self.val_script, "-"],
            input=json.dumps(report_with_string_evidence),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Failed validation: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
