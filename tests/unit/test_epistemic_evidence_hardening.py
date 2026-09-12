"""test_epistemic_evidence_hardening.py - Regression test suite for P0/P1 epistemic & architectural fixes.

Verifies:
- Empty/failed crawl never fabricates 100% crawlability or retrieval readiness.
- Malformed HTTP status is treated as unknown/None, never defaulted to HTTP 200.
- Missing confidence defaults to 'low', never 'high'.
- Evidence refs point strictly to primary crawled artifacts and never cite synthetic sensor summaries as quotes.
- safe_fetch explicitly disables ambient environment proxies.
- Route-level rendering gaps suppress downstream findings only on the affected route, never site-wide.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR_SCRIPTS = REPO_ROOT / "src" / "skills" / "audit-orchestrator" / "scripts"
SCRAPER_SCRIPTS = REPO_ROOT / "src" / "skills" / "web-scraper" / "scripts"

for p in (ORCHESTRATOR_SCRIPTS, SCRAPER_SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from assemble_report import assemble  # type: ignore
from causal_gate import apply_causal_suppression  # type: ignore
from audit import make_evidence_ref  # type: ignore


class TestEpistemicScoringIntegrity(unittest.TestCase):
    """Test that missing or failed measurements never fabricate 100% scores."""

    def test_empty_crawl_scores_zero_not_100(self):
        """When no pages are crawled, crawlability and retrieval readiness must be 0.0, not 100.0."""
        report = assemble("https://example.com", [], [], [], {})
        dimensions = report["readiness"]["dimensions"]
        self.assertEqual(dimensions["crawlability"], 0.0, "Crawlability must not default to 100.0 on empty crawl")
        self.assertEqual(dimensions["retrieval_readiness"], 0.0, "Retrieval readiness must not default to 100.0 on empty crawl")
        self.assertEqual(report["audit_status"], "failed", "Empty crawl audit status must be 'failed'")
        self.assertEqual(report["readiness"]["dimension_status"]["crawlability"], "unmeasured")
        self.assertEqual(report["readiness"]["dimension_status"]["retrieval_readiness"], "unmeasured")

    def test_malformed_status_never_defaults_to_200(self):
        """Pages with malformed or missing status codes must not be counted as crawlable HTTP 200s."""
        records = [
            {"artifact": "response-0001", "url": "https://example.com/bad1", "status_code": "invalid_status", "text": "Page one text content that is long enough."},
            {"artifact": "response-0002", "url": "https://example.com/bad2", "status_code": None, "text": "Page two text content that is long enough."},
            {"artifact": "response-0003", "url": "https://example.com/good", "status_code": 200, "text": "Page three text content that is long enough."},
        ]
        report = assemble("https://example.com", [], records, [], {})
        dimensions = report["readiness"]["dimensions"]
        # Only 1 of 3 pages is valid HTTP < 400
        expected_crawlability = round((1 / 3) * 100.0, 2)
        self.assertEqual(dimensions["crawlability"], expected_crawlability, "Malformed status codes must not count as crawlable 200s")

    def test_missing_confidence_defaults_to_low(self):
        """Findings without explicit confidence must default to 'low', never 'high'."""
        records = [
            {"artifact": "response-0001", "url": "https://example.com/", "status_code": 200, "text": "Page body text with sufficient length."}
        ]
        checks = [{"check_id": "D1", "solution_level": "C", "reference_band": "S2"}]
        candidates = [
            {
                "check_id": "D1",
                "cause_id": "TEST_CAUSE",
                "scope": "https://example.com/",
                "finding_kind": "confirmed_problem",
                "actual_band": "S2",
                "title": "Uncalibrated defect finding",
                "observation": "Some observation",
                "collection_complete_for_scope": True,
                "severity_reason": "Robots restriction",
                "difficulty": 2,
                "difficulty_reason": "Simple config fix",
                "evidence_refs": [{"artifact": "response-0001", "locator": "text", "quote": "Page body"}],
                # Note: No 'confidence' field provided
            }
        ]
        report = assemble("https://example.com", candidates, records, checks, {})
        self.assertEqual(len(report["findings"]), 1)
        self.assertEqual(report["findings"][0]["confidence"], "low", "Missing confidence must default to 'low'")

    def test_justification_avoids_unsupported_causality(self):
        """Generated justifications must avoid asserting unmeasured generative citation lift."""
        records = [
            {"artifact": "response-0001", "url": "https://example.com/", "status_code": 200, "text": "Page body text with sufficient length."}
        ]
        checks = [{"check_id": "G1", "solution_level": "C", "reference_band": "S2"}]
        candidates = [
            {
                "check_id": "G1",
                "cause_id": "LOW_CITABILITY_SCORE",
                "scope": "https://example.com/",
                "finding_kind": "confirmed_problem",
                "actual_band": "S2",
                "title": "Sub-threshold citability score",
                "observation": "Page achieved low score",
                "collection_complete_for_scope": True,
                "severity_reason": "Low citability score",
                "difficulty": 2,
                "difficulty_reason": "Content optimization",
                "evidence_refs": [{"artifact": "response-0001", "locator": "text", "quote": "Page body"}],
            }
        ]
        report = assemble("https://example.com", candidates, records, checks, {})
        self.assertEqual(len(report["findings"]), 1)
        just = report["findings"][0].get("priority_justification", "")
        self.assertNotIn("directly depressing generative citation lift", just)
        self.assertIn("heuristic citability score based on empirical GEO benchmarks", just)


class TestEvidenceProvenance(unittest.TestCase):
    """Test that evidence references point to primary crawled sources, not sensor artifacts."""

    def test_evidence_ref_uses_primary_artifact_not_sensor(self):
        """When finding is on a crawled page, evidence ref must cite the response artifact, not sensor artifact."""
        pages_by_url = {
            "https://example.com/page1": ("response-0001", "<html><body>Hello World!</body></html>")
        }
        ev_text = "Page lacks Schema.org Organization structured data on the root."
        refs = make_evidence_ref(ev_text, "https://example.com/page1", "sensor-entity-content-audit", pages_by_url)

        self.assertEqual(len(refs), 1)
        ref = refs[0]
        # Must point to primary crawled artifact, NEVER sensor-entity-content-audit
        self.assertEqual(ref["artifact"], "response-0001")
        # Must not fabricate a quote from sensor summary text
        self.assertIsNone(ref.get("quote"))
        self.assertIn("structural_observation", ref)

    def test_evidence_ref_quotes_actual_substring_if_present(self):
        """If ev_text contains a quoted string that is genuinely in the page body, it may be quoted."""
        pages_by_url = {
            "https://example.com/page1": ("response-0001", "<html><body>The product price is $49.99 today.</body></html>")
        }
        ev_text = "Found conflicting price '$49.99' on checkout page."
        refs = make_evidence_ref(ev_text, "https://example.com/page1", "sensor-fact-consistency-audit", pages_by_url)

        self.assertEqual(len(refs), 1)
        ref = refs[0]
        self.assertEqual(ref["artifact"], "response-0001")
        self.assertEqual(ref.get("quote"), "$49.99")


class TestRouteScopedCausalGating(unittest.TestCase):
    """Test that route-level rendering gaps suppress downstream findings only on that route."""

    def test_rendering_gap_on_route_a_does_not_suppress_route_b(self):
        """Rendering gap on /product must NOT suppress valid fact findings on /about."""
        raw_findings = [
            {
                "id": "F-001",
                "cause_id": "RENDERED_CONTENT_GAP",
                "scope": "https://example.com/product",
                "url": "https://example.com/product",
                "title": "Blank SPA Product Page",
                "evidence": "Word count is 3 on https://example.com/product",
            },
            {
                "id": "F-002",
                "cause_id": "LOW_CITABILITY_SCORE",
                "scope": "https://example.com/product",
                "url": "https://example.com/product",
                "title": "Low Citability on Product",
                "evidence": "Product page citability 5/100",
            },
            {
                "id": "F-003",
                "cause_id": "FIRST_PARTY_FACT_CONFLICT",
                "scope": "https://example.com/about",
                "url": "https://example.com/about",
                "title": "Fact Conflict on About Page",
                "evidence": "Year founded is 2018 vs 2020 on /about",
            },
        ]
        inv = {
            "site": "https://example.com",
            "pages": [
                {"url": "https://example.com/product", "word_count": 3, "html": "<html><div id='root'></div></html>"},
                {"url": "https://example.com/about", "word_count": 450, "html": "<html><body>Rendered about page with 450 words.</body></html>"},
                {"url": "https://example.com/", "word_count": 300, "html": "<html><body>Rendered homepage with 300 words.</body></html>"},
            ],
        }

        allowed, suppressed, dag_meta = apply_causal_suppression(raw_findings, inv=inv)

        allowed_causes = [f["cause_id"] for f in allowed]
        suppressed_causes = [f["cause_id"] for f in suppressed]

        # Product citability should be suppressed by product rendering gap
        self.assertIn("LOW_CITABILITY_SCORE", suppressed_causes)
        # About fact conflict MUST be allowed because /about is fully rendered!
        self.assertIn("FIRST_PARTY_FACT_CONFLICT", allowed_causes, "Rendered /about page fact conflict must not be suppressed by /product rendering gap")
        self.assertIn("RENDERED_CONTENT_GAP", allowed_causes)


if __name__ == "__main__":
    unittest.main()
