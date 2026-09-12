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

    def test_reject_boolean_as_integer_or_number(self):
        """Failure test: Boolean True/False cannot pass as integer or number."""
        report = json.loads(json.dumps(VALID_SCHEMA_REPORT))
        report["summary"]["total_findings"] = True
        res = run_validator(report)
        self.assertNotEqual(res.returncode, 0)

    def test_recommended_public_report_contract_validates(self):
        """Success test: The user's exact recommended top-tier public JSON report contract validates cleanly."""
        recommended_report = {
            "schema_version": "1.0.0",
            "site": "https://example.com",
            "audited_at": "2026-09-10T12:00:00Z",
            "audit_status": "complete",
            "summary": {
                "total_findings": 3,
                "critical": 0,
                "high": 1,
                "medium": 1,
                "low": 1,
            },
            "findings": [
                {
                    "id": "F-001",
                    "title": "Conflicting Product Pricing Across First-Party Pages",
                    "severity": "high",
                    "category": "fact_consistency",
                    "root_cause": "The same product is represented with conflicting current prices across first-party sources.",
                    "confidence": "high",
                    "scope": {
                        "type": "entity",
                        "entity": "Example Product",
                        "attribute": "price",
                        "locale": "en-US",
                    },
                    "evidence": {
                        "summary": "Two first-party sources expose different prices for the same product.",
                        "sources": [
                            {
                                "url": "https://example.com/product",
                                "type": "first_party",
                                "observation": "Visible product price is $999.",
                            },
                            {
                                "url": "https://example.com/pricing",
                                "type": "first_party",
                                "observation": "Visible product price is $1099.",
                            },
                        ],
                    },
                    "impact": "Conflicting first-party representations reduce confidence in which product price should be treated as current when the brand is represented in AI-assisted discovery.",
                    "suggested_action": {
                        "summary": "Establish one authoritative current pricing representation and synchronize all applicable surfaces.",
                        "priority": "high",
                        "technical_fix": "Synchronize visible pricing, structured Product/Offer data, and relevant first-party endpoints with the authoritative price source. Preserve currency and billing interval explicitly.",
                        "creative_fix": "Present the price consistently with clear currency, billing interval, applicable variant, and pricing conditions.",
                        "verification": "Re-run the audit and verify that all applicable first-party sources resolve to the same current price for the same entity, variant, locale, and billing interval.",
                    },
                },
                {
                    "id": "F-002",
                    "title": "Weak Intent-to-Landing Context Continuity",
                    "severity": "medium",
                    "category": "engagement",
                    "root_cause": "The candidate landing experience does not clearly preserve the informational context associated with the user intent represented by the referring query.",
                    "confidence": "medium",
                    "scope": {
                        "type": "page",
                        "url": "https://example.com/products/example",
                    },
                    "evidence": {
                        "summary": "The landing page provides limited early-page evidence connecting the page to the evaluated user intent.",
                        "sources": [
                            {
                                "url": "https://example.com/products/example",
                                "type": "visible_content",
                                "observation": "The primary heading and early-page content provide limited explicit context for the evaluated intent.",
                            }
                        ],
                    },
                    "impact": "A visitor arriving with a specific intent may need additional interpretation or navigation before confirming that the page addresses the original need.",
                    "suggested_action": {
                        "summary": "Make the landing page immediately communicate the relationship between the user's intent and the page's content.",
                        "priority": "medium",
                        "technical_fix": "Ensure the page exposes an unambiguous title, canonical URL, structured metadata, and machine-readable content corresponding to the page's actual purpose.",
                        "creative_fix": "Strengthen the primary heading, introductory copy, and first relevant action so the page immediately confirms the user's intended task.",
                        "verification": "Re-run the intent-to-landing analysis and confirm stronger alignment between the expected intent, page purpose, relevant facts, and next action.",
                    },
                },
                {
                    "id": "F-003",
                    "title": "Limited Machine-Readable Entity Evidence",
                    "severity": "low",
                    "category": "entity_content",
                    "root_cause": "Important entity attributes are not consistently represented in the machine-readable evidence observed on the audited page.",
                    "confidence": "medium",
                    "scope": {
                        "type": "page",
                        "url": "https://example.com/product/example",
                    },
                    "evidence": {
                        "summary": "The page exposes incomplete structured evidence for the detected entity.",
                        "sources": [
                            {
                                "url": "https://example.com/product/example",
                                "type": "structured_data",
                                "observation": "Observed Product structured data does not expose all expected attributes for the detected entity.",
                            }
                        ],
                    },
                    "impact": "Incomplete structured representation can make entity attributes less explicit for downstream machine interpretation.",
                    "suggested_action": {
                        "summary": "Complete the structured representation for attributes that are actually supported by the page.",
                        "priority": "low",
                        "technical_fix": "Add accurate Schema.org properties supported by the page and keep structured values synchronized with visible content.",
                        "creative_fix": None,
                        "verification": "Re-run structured-data extraction and verify that each emitted attribute is present, accurate, entity-bound, and consistent with visible first-party content.",
                    },
                },
            ],
            "proactive_actions": [
                {
                    "id": "P-001",
                    "title": "Establish a Canonical Fact Source",
                    "category": "fact_governance",
                    "summary": "Define authoritative first-party sources for high-value entity attributes and keep derived representations synchronized.",
                    "priority": "medium",
                    "technical_fix": "Maintain a canonical source for important attributes such as price, availability, contact details, and lifecycle status, and validate derived representations against it.",
                    "creative_fix": "Use consistent terminology and contextual labels for important facts across major customer-facing pages.",
                    "verification": "Run periodic cross-source consistency checks and confirm that important facts resolve to one current authoritative representation.",
                }
            ],
            "limitations": [
                "No JavaScript browser rendering was performed.",
                "Findings are based only on resources successfully acquired during this audit.",
                "Robots.txt observations represent declared crawler permissions and do not prove search inclusion, indexing, ranking, or citation.",
                "No claim is made about actual citation or placement by a specific AI assistant.",
                "Engagement observations are content/navigation proxies unless external behavioral analytics are explicitly supplied.",
            ],
        }
        res = run_validator(recommended_report)
        self.assertEqual(res.returncode, 0, f"Validator failed on recommended report: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
