#!/usr/bin/env python3
"""
test_sensor_standalone_fetch.py - Unit tests verifying standalone sensor safe_fetch unpacking,
priority-descending finding ordering, and dimensions omission in deliverable reports.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Path bootstrap
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILLS_DIR = os.path.join(PROJECT_ROOT, "src", "skills")
for _p in [
    os.path.join(SKILLS_DIR, "audit-orchestrator", "scripts"),
    os.path.join(SKILLS_DIR, "web-scraper", "scripts"),
    os.path.join(SKILLS_DIR, "discoverability-audit", "scripts"),
    os.path.join(SKILLS_DIR, "entity-content-audit", "scripts"),
    os.path.join(SKILLS_DIR, "fact-consistency-audit", "scripts"),
    os.path.join(SKILLS_DIR, "corroboration-authority-audit", "scripts"),
    os.path.join(SKILLS_DIR, "geo-content-audit", "scripts"),
    os.path.join(SKILLS_DIR, "engagement-context-audit", "scripts"),
]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

import corroboration_check  # type: ignore
import discoverability_check  # type: ignore
import entity_content_check  # type: ignore
import fact_consistency_check  # type: ignore
import orchestrator  # type: ignore
from validate_report import validate_report_dict  # type: ignore


class TestSensorStandaloneFetchUnpacking(unittest.TestCase):
    """Test that all 4 sensor scripts unpack safe_fetch 4-tuples correctly in standalone mode."""

    def test_discoverability_standalone_safe_fetch(self):
        """discoverability_check must unpack safe_fetch return tuple without ValueError."""
        def mock_fetch(url, **kwargs):
            if "robots.txt" in url:
                return (200, "User-agent: *\nAllow: /", {"content-type": "text/plain"}, "")
            if "llms.txt" in url:
                return (200, "# LLMS Title\n> Summary\n- [Link](https://example.com/)", {"content-type": "text/plain"}, "")
            return (200, "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>", {"content-type": "text/html"}, "")

        with patch.object(discoverability_check, "safe_fetch", side_effect=mock_fetch):
            result = discoverability_check.audit("https://example.com", "example.com", inv=None)
            self.assertIn(result.get("status"), ["ok", "inconclusive"])
            self.assertIsInstance(result.get("findings"), list)

    def test_corroboration_standalone_safe_fetch(self):
        """corroboration_check must assign HTML body string, not headers dict, in standalone mode."""
        mock_html = '<html><body><a href="https://www.wikidata.org/wiki/Q12345" rel="me">Wiki</a></body></html>'
        with patch.object(corroboration_check, "safe_fetch", return_value=(200, mock_html, {"content-type": "text/html"}, "")):
            result = corroboration_check.audit("https://example.com", "example.com", inv=None)
            self.assertIn(result.get("status"), ["ok", "inconclusive"])
            self.assertIsInstance(result.get("findings"), list)

    def test_entity_content_standalone_safe_fetch(self):
        """entity_content_check must assign HTML body string, not headers dict, in standalone mode."""
        mock_html = '<html><head><title>Test Store</title></head><body><h1>Product</h1></body></html>'
        with patch.object(entity_content_check, "safe_fetch", return_value=(200, mock_html, {"content-type": "text/html"}, "")):
            result = entity_content_check.audit("https://example.com", "example.com", inv=None)
            self.assertIn(result.get("status"), ["ok", "inconclusive"])
            self.assertIsInstance(result.get("findings"), list)

    def test_fact_consistency_standalone_safe_fetch(self):
        """fact_consistency_check must assign HTML body string, not headers dict, in standalone mode."""
        mock_html = '<html><body><p>Price: $49.99</p><footer>Copyright 2025</footer></body></html>'
        with patch.object(fact_consistency_check, "safe_fetch", return_value=(200, mock_html, {"content-type": "text/html"}, "")):
            result = fact_consistency_check.audit("https://example.com", "example.com", inv=None)
            self.assertIn(result.get("status"), ["ok", "inconclusive"])
            self.assertIsInstance(result.get("findings"), list)


class TestPriorityOrderingAndDimensionsOmission(unittest.TestCase):
    """Test priority-ranked ordering and removal of dimensions in final deliverable reports."""

    def test_explicit_agent_priority_rank_honored(self):
        """Findings with priority_rank in review must be sorted in that exact priority order."""
        inv = {
            "site": "https://example.com",
            "pages": [{"url": "https://example.com/", "status": 200, "word_count": 100}],
        }
        review = {
            "findings": [
                {
                    "cause_id": "INERT_CTA_TARGET",
                    "title": "Low priority CTA defect",
                    "severity": "low",
                    "category": "engagement_context",
                    "root_cause": "Anchor points to inert hash",
                    "confidence": "high",
                    "scope": "https://example.com/",
                    "evidence": "Inert anchor detected",
                    "impact": "Visitors cannot convert",
                    "suggested_action": {
                        "summary": "Fix CTA link destination",
                        "technical_fix": "Set href to /pricing",
                        "creative_fix": "Add clear action copy",
                        "priority": "low",
                        "verification": "Test link click",
                    },
                    "priority_rank": 2,
                },
                {
                    "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                    "title": "Top priority Entity schema defect",
                    "severity": "medium",
                    "category": "entity_content",
                    "root_cause": "Missing Organization JSON-LD",
                    "confidence": "high",
                    "scope": "https://example.com/",
                    "evidence": "No JSON-LD found",
                    "impact": "Brand identity unresolvable",
                    "suggested_action": {
                        "summary": "Add Schema.org Organization",
                        "technical_fix": "Embed Organization JSON-LD",
                        "creative_fix": "State legal name",
                        "priority": "medium",
                        "verification": "Test with Schema.org validator",
                    },
                    "priority_rank": 1,
                },
            ]
        }
        report = orchestrator.synthesize_audit_report("https://example.com", inv, {}, review=review)
        findings = report.get("findings", [])
        self.assertEqual(len(findings), 2)
        # Priority Rank 1 must be first
        self.assertEqual(findings[0]["id"], "F-001")
        self.assertEqual(findings[0]["priority_rank"], 1)
        self.assertEqual(findings[0]["title"], "Top priority Entity schema defect")
        # Priority Rank 2 must be second
        self.assertEqual(findings[1]["id"], "F-002")
        self.assertEqual(findings[1]["priority_rank"], 2)
        self.assertEqual(findings[1]["title"], "Low priority CTA defect")

    def test_dimensions_omitted_in_reviewed_final_report(self):
        """Reviewed report readiness must omit dimensions but retain composite_score and grade."""
        inv = {
            "site": "https://example.com",
            "pages": [{"url": "https://example.com/", "status": 200, "word_count": 100}],
        }
        review = {"findings": []}
        report = orchestrator.synthesize_audit_report("https://example.com", inv, {}, review=review)
        readiness = report.get("readiness")
        self.assertIsNotNone(readiness)
        self.assertIn("composite_score", readiness)
        self.assertIn("grade", readiness)
        self.assertNotIn("dimensions", readiness, "dimensions must be omitted from reviewed report readiness")

        # Must validate cleanly against report-schema.json
        valid, errors = validate_report_dict(report)
        self.assertTrue(valid, f"Reviewed report failed validation: {errors}")

    def test_sanitize_clean_report_omits_dimensions(self):
        """sanitize_clean_report with include_scores=True must not include dimensions."""
        inv = {
            "site": "https://example.com",
            "pages": [{"url": "https://example.com/", "status": 200, "word_count": 100}],
        }
        report = orchestrator.synthesize_audit_report("https://example.com", inv, {})
        # Internal report before sanitization has dimensions
        self.assertIn("dimensions", report.get("readiness", {}))

        clean = orchestrator.sanitize_clean_report(report, include_scores=True)
        clean_readiness = clean.get("readiness", {})
        self.assertIn("composite_score", clean_readiness)
        self.assertIn("grade", clean_readiness)
        self.assertNotIn("dimensions", clean_readiness, "sanitize_clean_report must omit dimensions")

        valid, errors = validate_report_dict(clean)
        self.assertTrue(valid, f"Clean report failed validation: {errors}")


if __name__ == "__main__":
    unittest.main()
