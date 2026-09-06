"""Unit tests for validate_report.py Draft-07 JSON Schema Gate."""

import json
import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.fixtures.report_fixtures import (
    INVALID_SEVERITY_REPORT,
    MISSING_REQUIRED_FIELD_REPORT,
    NON_INTEGER_SUMMARY_REPORT,
    VALID_SCHEMA_REPORT,
    VALID_STRING_EVIDENCE_REPORT,
)
from tests.helpers.cli_runner import run_validator


class TestValidateReport(unittest.TestCase):
    """Verifies Draft-07 JSON report schema gate validation."""

    def test_valid_structured_evidence_report_passes(self):
        """Success test: Fully structured audit report passes schema gate."""
        res = run_validator(VALID_SCHEMA_REPORT)
        self.assertEqual(res.returncode, 0, f"Validator failed with stderr: {res.stderr}")

    def test_valid_string_evidence_report_passes(self):
        """Success test: Report with string evidence (Round 3 PS format) passes schema gate."""
        res = run_validator(VALID_STRING_EVIDENCE_REPORT)
        self.assertEqual(res.returncode, 0, f"Validator failed with stderr: {res.stderr}")

    def test_invalid_severity_fails(self):
        """Failure test: Disallowed severity value ('info') fails validation."""
        res = run_validator(INVALID_SEVERITY_REPORT)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("validation failed", res.stderr.lower())

    def test_missing_required_fields_fails(self):
        """Failure test: Report missing required keys ('audited_at', 'summary', 'findings') fails."""
        res = run_validator(MISSING_REQUIRED_FIELD_REPORT)
        self.assertNotEqual(res.returncode, 0)

    def test_non_integer_summary_counts_fails(self):
        """Failure test: Non-integer total_findings count fails validation."""
        res = run_validator(NON_INTEGER_SUMMARY_REPORT)
        self.assertNotEqual(res.returncode, 0)

    def test_malformed_json_input_fails(self):
        """Failure test: Malformed JSON syntax rejected with non-zero exit code."""
        res = run_validator("{ broken json ,,,")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid json", res.stderr.lower())

    def test_empty_input_fails(self):
        """Failure test: Empty input rejected with non-zero exit code."""
        res = run_validator("")
        self.assertNotEqual(res.returncode, 0)

    def test_reject_extra_root_properties(self):
        """Failure test: unexpected root properties rejected when additionalProperties is false."""
        bad_report = dict(VALID_SCHEMA_REPORT)
        bad_report["unexpected_extra_property"] = "disallowed"
        res = run_validator(bad_report)
        self.assertNotEqual(res.returncode, 0)

    def test_reject_negative_summary_counts(self):
        """Failure test: Negative numbers in summary counts are rejected."""
        bad_report = json.loads(json.dumps(VALID_SCHEMA_REPORT))
        bad_report["summary"]["total_findings"] = -1
        res = run_validator(bad_report)
        self.assertNotEqual(res.returncode, 0)

    def test_accept_null_creative_fix(self):
        """Success test: creative_fix can be null while technical_fix is string."""
        report = json.loads(json.dumps(VALID_SCHEMA_REPORT))
        report["findings"][0]["suggested_action"]["creative_fix"] = None
        res = run_validator(report)
        self.assertEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
