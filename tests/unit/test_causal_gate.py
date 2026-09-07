"""Unit tests for causal_gate.py Monotonic Causal DAG & Epistemic Falsification Engine."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ORCH_SCRIPTS = os.path.join(PROJECT_ROOT, "src", "skills", "audit-orchestrator", "scripts")
if ORCH_SCRIPTS not in sys.path:
    sys.path.insert(0, ORCH_SCRIPTS)

from causal_gate import (
    apply_causal_suppression,
    build_evidence_index,
    evaluate_epistemic_state,
)


class TestCausalGate(unittest.TestCase):
    """Verifies monotonic causal suppression, epistemic state derivation, and evidence indexing."""

    def test_layer0_block_suppresses_downstream_symptoms(self):
        """Layer 0 access block (e.g. AI_RETRIEVAL_BLOCKED) must suppress schema and citability findings."""
        raw_findings = [
            {"id": "F-001", "cause_id": "AI_RETRIEVAL_BLOCKED", "severity": "critical", "title": "Retrieval Blocked"},
            {"id": "F-002", "cause_id": "MATERIAL_ENTITY_AMBIGUITY", "severity": "high", "title": "No Schema"},
            {"id": "F-003", "cause_id": "LOW_CITABILITY_SCORE", "severity": "medium", "title": "Low Citability"},
            {"id": "F-004", "cause_id": "FIRST_PARTY_FACT_CONFLICT", "severity": "high", "title": "Fact Conflict"},
        ]

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings)

        self.assertTrue(dag_metadata["has_layer0_block"])
        self.assertEqual(len(allowed), 1)
        self.assertEqual(allowed[0]["cause_id"], "AI_RETRIEVAL_BLOCKED")
        self.assertEqual(len(suppressed), 3)
        suppressed_ids = [f["cause_id"] for f in suppressed]
        self.assertIn("MATERIAL_ENTITY_AMBIGUITY", suppressed_ids)
        self.assertIn("LOW_CITABILITY_SCORE", suppressed_ids)
        self.assertIn("FIRST_PARTY_FACT_CONFLICT", suppressed_ids)

    def test_layer1_rendering_gap_suppresses_citability_and_facts(self):
        """Layer 1 rendering gap must suppress citability and fact checks, but allow entity findings."""
        raw_findings = [
            {"id": "F-001", "cause_id": "RENDERED_CONTENT_GAP", "severity": "high", "title": "Blank SPA Shell"},
            {"id": "F-002", "cause_id": "MATERIAL_ENTITY_AMBIGUITY", "severity": "high", "title": "No Schema"},
            {"id": "F-003", "cause_id": "LOW_CITABILITY_SCORE", "severity": "medium", "title": "Low Citability"},
            {"id": "F-004", "cause_id": "FIRST_PARTY_FACT_CONFLICT", "severity": "high", "title": "Fact Conflict"},
        ]

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings)

        self.assertFalse(dag_metadata["has_layer0_block"])
        self.assertTrue(dag_metadata["has_layer1_rendering_gap"])
        allowed_ids = [f["cause_id"] for f in allowed]
        self.assertIn("RENDERED_CONTENT_GAP", allowed_ids)
        self.assertIn("MATERIAL_ENTITY_AMBIGUITY", allowed_ids)
        suppressed_ids = [f["cause_id"] for f in suppressed]
        self.assertIn("LOW_CITABILITY_SCORE", suppressed_ids)
        self.assertIn("FIRST_PARTY_FACT_CONFLICT", suppressed_ids)

    def test_clean_site_allows_all_findings(self):
        """When no Layer 0 or Layer 1 root defect exists, all findings pass through."""
        raw_findings = [
            {"id": "F-001", "cause_id": "MATERIAL_ENTITY_AMBIGUITY", "severity": "high", "title": "No Schema"},
            {"id": "F-002", "cause_id": "LOW_CITABILITY_SCORE", "severity": "medium", "title": "Low Citability"},
        ]

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings)

        self.assertFalse(dag_metadata["has_layer0_block"])
        self.assertFalse(dag_metadata["has_layer1_rendering_gap"])
        self.assertEqual(len(allowed), 2)
        self.assertEqual(len(suppressed), 0)

    def test_evaluate_epistemic_state_derivation(self):
        """Epistemic state evaluates to observed, gap, or suppressed correctly."""
        inv_clean = {
            "pages": [
                {"url": "https://example.com/", "status": 200, "word_count": 250, "snr": 0.4}
            ]
        }
        specialist_clean = {
            "discoverability-audit": {"coverage": {"retrieval_bots_allowed": 7, "visible_words_initial_html": 250}},
            "entity-content-audit": {"coverage": {"jsonld_present": True}},
            "fact-consistency-audit": {"coverage": {"facts_checked": 10}},
            "corroboration-authority-audit": {"coverage": {"sameas_declared": 2}},
            "geo-content-audit": {"coverage": {"average_citability_score": 78.0}},
            "engagement-context-audit": {"coverage": {"pages_evaluated": 1}},
        }

        state = evaluate_epistemic_state(inv_clean, specialist_clean)
        self.assertEqual(state["retrieval"], "observed")
        self.assertEqual(state["rendering"], "observed")
        self.assertEqual(state["entity"], "observed")
        self.assertEqual(state["facts"], "observed")
        self.assertEqual(state["corroboration"], "observed")
        self.assertEqual(state["geo"], "observed")
        self.assertEqual(state["engagement"], "observed")

    def test_build_evidence_index_generates_sequential_ids(self):
        """Evidence index creates sequential EV-XXX identifiers with route and kind."""
        inv = {
            "robots": {"summary": {"*": "allow"}},
            "pages": [{"url": "https://example.com/", "status": 200, "word_count": 100, "snr": 0.3}],
        }
        specialist = {
            "entity-content-audit": {"coverage": {"types_declared": ["Organization"]}},
            "corroboration-authority-audit": {"coverage": {"probes": [{"target_url": "https://wikidata.org/Q1", "probe_result": "ok"}]}},
            "fact-consistency-audit": {"coverage": {"facts_checked": 5, "fact_conflicts": 0}},
        }

        evidence = build_evidence_index(inv, specialist)
        self.assertGreaterEqual(len(evidence), 4)
        self.assertEqual(evidence[0]["id"], "EV-001")
        self.assertEqual(evidence[1]["id"], "EV-002")
        self.assertEqual(evidence[0]["kind"], "robots")
        for ev in evidence:
            self.assertIn("route", ev)
            self.assertIn("observation", ev)


if __name__ == "__main__":
    unittest.main()
