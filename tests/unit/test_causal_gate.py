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
    DEFAULT_LIMITATIONS,
    ROOT_CAUSE_PRECEDENCE,
    apply_causal_suppression,
    build_evidence_index,
    compute_archetype_confidence,
    compute_severity_score,
    evaluate_causal_nodes,
    evaluate_epistemic_state,
    severity_from_score,
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

    def test_compute_severity_score_and_mapping(self):
        """Severity score formula bounds factors and maps to correct severity categories."""
        # Maximum factors: 100 * 1.0 * (0.35 + 0.30 + 0.20 + 0.15) = 100.0 -> critical
        score_max = compute_severity_score(1.0, 1.0, 1.0, 1.0, 1.0)
        self.assertEqual(score_max, 100.0)
        self.assertEqual(severity_from_score(score_max), "critical")

        # High severity: 70.0 -> high
        score_high = compute_severity_score(0.9, 0.8, 0.8, 0.7, 0.8)
        self.assertGreaterEqual(score_high, 65.0)
        self.assertEqual(severity_from_score(score_high), "high")

        # Medium severity
        score_med = compute_severity_score(0.8, 0.6, 0.6, 0.6, 0.6)
        self.assertTrue(40.0 <= score_med < 65.0)
        self.assertEqual(severity_from_score(score_med), "medium")

        # Low severity
        score_low = compute_severity_score(0.5, 0.2, 0.2, 0.2, 0.2)
        self.assertTrue(score_low < 40.0)
        self.assertEqual(severity_from_score(score_low), "low")

    def test_compute_archetype_confidence(self):
        """Archetype confidence weights route (40%), vocab (25%), schema (20%), and commercial (15%)."""
        conf_perfect = compute_archetype_confidence(1.0, 1.0, 1.0, 1.0)
        self.assertEqual(conf_perfect, 1.0)

        # Route heavy
        conf_route = compute_archetype_confidence(1.0, 0.0, 0.0, 0.0)
        self.assertEqual(conf_route, 0.40)

        # Below 0.60 threshold
        conf_low = compute_archetype_confidence(0.5, 0.4, 0.3, 0.2)
        self.assertLess(conf_low, 0.60)

    def test_default_limitations_and_precedence(self):
        """DEFAULT_LIMITATIONS and ROOT_CAUSE_PRECEDENCE are defined and non-empty."""
        self.assertEqual(len(DEFAULT_LIMITATIONS), 4)
        self.assertIn("No JavaScript browser rendering was performed.", DEFAULT_LIMITATIONS)
        self.assertEqual(len(ROOT_CAUSE_PRECEDENCE), 8)
        self.assertEqual(ROOT_CAUSE_PRECEDENCE[0], "SITE_UNAVAILABLE_OR_BLOCKED")
        self.assertEqual(ROOT_CAUSE_PRECEDENCE[1], "AI_RETRIEVAL_BLOCKED")

    def test_evaluate_causal_nodes(self):
        """evaluate_causal_nodes returns 8 core nodes in confirmed_pass/fail/unknown."""
        inv = {
            "pages": [{"url": "https://example.com/", "status": 200, "word_count": 500, "snr": 0.5}],
        }
        specialist = {
            "discoverability-audit": {"coverage": {"retrieval_bots_allowed": 5}},
            "entity-content-audit": {"coverage": {"jsonld_present": True}},
            "fact-consistency-audit": {"coverage": {"facts_checked": 10, "fact_conflicts": 0}},
            "geo-content-audit": {"coverage": {"average_citability_score": 85.0}},
            "engagement-context-audit": {"coverage": {"pages_evaluated": 1}},
        }
        nodes = evaluate_causal_nodes(inv, specialist)
        self.assertEqual(nodes["reachability"], "confirmed_pass")
        self.assertEqual(nodes["retrieval_access"], "confirmed_pass")
        self.assertEqual(nodes["static_readability"], "confirmed_pass")
        self.assertEqual(nodes["entity_explicitness"], "confirmed_pass")
        self.assertEqual(nodes["fact_consistency"], "confirmed_pass")
        self.assertEqual(nodes["citability"], "confirmed_pass")
        self.assertEqual(nodes["on_site_orientation"], "confirmed_pass")
        self.assertEqual(nodes["engagement_handoff"], "confirmed_pass")

    def test_evaluate_causal_nodes_orientation_and_handoff_failures(self):
        """Verify on_site_orientation and engagement_handoff set to confirmed_fail when defect findings present."""
        inv = {
            "pages": [{"url": "https://example.com/", "status": 200, "word_count": 500, "snr": 0.5}],
        }
        # 1. Orientation failure via LOW_INFORMATION_SCENT
        spec_orientation_fail = {
            "engagement-context-audit": {
                "coverage": {"pages_evaluated": 1},
                "findings": [{"cause_id": "LOW_INFORMATION_SCENT", "title": "Low Scent"}],
            }
        }
        nodes1 = evaluate_causal_nodes(inv, spec_orientation_fail)
        self.assertEqual(nodes1["on_site_orientation"], "confirmed_fail")
        self.assertEqual(nodes1["engagement_handoff"], "confirmed_pass")

        # 2. Handoff failure via CTA_REACHABILITY_FRICTION
        spec_handoff_fail = {
            "engagement-context-audit": {
                "coverage": {"pages_evaluated": 1},
                "findings": [{"cause_id": "CTA_REACHABILITY_FRICTION", "title": "Hidden CTA"}],
            }
        }
        nodes2 = evaluate_causal_nodes(inv, spec_handoff_fail)
        self.assertEqual(nodes2["on_site_orientation"], "confirmed_pass")
        self.assertEqual(nodes2["engagement_handoff"], "confirmed_fail")

        # 3. Both failures via GENERIC_H1 and INTENT_TO_LANDING_MISMATCH
        spec_both_fail = {
            "engagement-context-audit": {
                "coverage": {"pages_evaluated": 2},
                "findings": [
                    {"cause_id": "GENERIC_H1", "title": "Generic H1"},
                    {"cause_id": "INTENT_TO_LANDING_MISMATCH", "title": "Intent Mismatch"},
                ],
            }
        }
        nodes3 = evaluate_causal_nodes(inv, spec_both_fail)
        self.assertEqual(nodes3["on_site_orientation"], "confirmed_fail")
        self.assertEqual(nodes3["engagement_handoff"], "confirmed_fail")

    def test_taxonomy_alias_synchronization_in_suppression(self):
        """Verify causal suppression recognizes both canonical and alias names."""
        raw_findings = [
            {"id": "F-001", "cause_id": "META_DIRECTIVE_CONFLICT", "severity": "critical", "title": "Meta Directive Conflict"},
            {"id": "F-002", "cause_id": "UNVERIFIED_AUTHORITY_GAP", "severity": "high", "title": "No sameAs"},
            {"id": "F-003", "cause_id": "SUB_THRESHOLD_CITABILITY", "severity": "medium", "title": "Sub threshold citability"},
            {"id": "F-004", "cause_id": "TEMPORAL_DRIFT_DETECTED", "severity": "low", "title": "Stale copyright"},
            {"id": "F-005", "cause_id": "COMMERCIAL_HANDOFF_DISCONTINUITY", "severity": "medium", "title": "Handoff gap"},
            {"id": "F-006", "cause_id": "ABOVE_FOLD_ACTION_DELAY", "severity": "medium", "title": "Action delay"},
        ]

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings)
        self.assertTrue(dag_metadata["has_layer0_block"])
        self.assertEqual(len(allowed), 1)
        self.assertEqual(allowed[0]["cause_id"], "META_DIRECTIVE_CONFLICT")
        self.assertEqual(len(suppressed), 5)
        suppressed_cids = {f["cause_id"] for f in suppressed}
        self.assertIn("UNVERIFIED_AUTHORITY_GAP", suppressed_cids)
        self.assertIn("SUB_THRESHOLD_CITABILITY", suppressed_cids)
        self.assertIn("TEMPORAL_DRIFT_DETECTED", suppressed_cids)
        self.assertIn("COMMERCIAL_HANDOFF_DISCONTINUITY", suppressed_cids)
        self.assertIn("ABOVE_FOLD_ACTION_DELAY", suppressed_cids)

    def test_bidirectional_alias_suppression(self):
        """Verify canonical blockers suppress alias symptoms and alias blockers suppress canonical symptoms."""
        # 1. Canonical blocker (NOINDEX_EXCLUSION) suppressing alias symptoms
        findings1 = [
            {"id": "NOINDEX_EXCLUSION", "severity": "critical"},
            {"id": "WEAK_IDENTITY_SIGNALS", "severity": "high"},
            {"id": "LOW_CITABILITY_SCORE", "severity": "medium"},
            {"id": "CONTENT_RECENCY_DEFICIT", "severity": "low"},
        ]
        allowed1, suppressed1, _ = apply_causal_suppression(findings1)
        self.assertEqual(len(allowed1), 1)
        self.assertEqual(len(suppressed1), 3)

        # 2. Alias blocker (META_DIRECTIVE_CONFLICT) suppressing canonical symptoms
        findings2 = [
            {"cause_id": "META_DIRECTIVE_CONFLICT", "severity": "critical"},
            {"cause_id": "UNVERIFIED_AUTHORITY_GAP", "severity": "high"},
            {"cause_id": "SUB_THRESHOLD_CITABILITY", "severity": "medium"},
            {"cause_id": "TEMPORAL_DRIFT_DETECTED", "severity": "low"},
        ]
        allowed2, suppressed2, _ = apply_causal_suppression(findings2)
        self.assertEqual(len(allowed2), 1)
        self.assertEqual(len(suppressed2), 3)

    def test_orientation_and_handoff_with_id_field(self):
        """Verify orientation and handoff fail triggers work when trigger code is stored in 'id' field instead of 'cause_id'."""
        inv = {"pages": [{"url": "https://example.com/", "status": 200, "word_count": 500, "snr": 0.5}]}
        spec = {
            "engagement-context-audit": {
                "coverage": {"pages_evaluated": 1},
                "findings": [
                    {"id": "LOW_INFORMATION_SCENT", "title": "Low Scent"},
                    {"id": "VIEWPORT_ANSWER_ABSENCE", "title": "No answer in viewport"},
                ],
            }
        }
        nodes = evaluate_causal_nodes(inv, spec)
        self.assertEqual(nodes["on_site_orientation"], "confirmed_fail")
        self.assertEqual(nodes["engagement_handoff"], "confirmed_fail")

    def test_route_level_rendering_gap_suppression_and_nesting(self):
        """Route-level RENDERED_CONTENT_GAP must suppress downstream symptoms on that route and nest them."""
        raw_findings = [
            {
                "id": "F-001",
                "cause_id": "RENDERED_CONTENT_GAP",
                "scope": "https://example.com/en/products/default",
                "severity": "high",
                "title": "Blank SPA Shell on Product Route",
            },
            {
                "id": "F-002",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "scope": "https://example.com/en/products/default",
                "severity": "high",
                "title": "No Product Schema",
            },
            {
                "id": "F-003",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "scope": "https://example.com/en/products/default",
                "severity": "medium",
                "title": "Delayed CTA on Product Route",
            },
            {
                "id": "F-004",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "scope": "https://example.com/pricing",
                "severity": "medium",
                "title": "Delayed CTA on Rendered Pricing Route",
            },
        ]
        inv = {
            "pages": [
                {"url": "https://example.com/", "page_type": "homepage", "word_count": 400, "snr": 0.4},
                {"url": "https://example.com/en/products/default", "page_type": "product", "word_count": 3, "snr": 0.01},
                {"url": "https://example.com/pricing", "page_type": "pricing", "word_count": 350, "snr": 0.35},
            ]
        }

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings, inv=inv)

        self.assertFalse(dag_metadata["is_site_wide_rendering_gap"])
        allowed_scopes = [f.get("scope") for f in allowed]
        self.assertIn("https://example.com/en/products/default", allowed_scopes)
        self.assertIn("https://example.com/pricing", allowed_scopes)

        # F-002 and F-003 on /en/products/default must be suppressed
        suppressed_ids = [f["cause_id"] for f in suppressed]
        self.assertIn("ATTRIBUTE_INCOMPLETENESS", suppressed_ids)
        self.assertIn("CTA_REACHABILITY_FRICTION", suppressed_ids)
        self.assertEqual(len(suppressed), 2)

        # Downstream symptoms must be nested under F-001 (the keystone)
        keystone = next(f for f in allowed if f["id"] == "F-001")
        self.assertIn("downstream_symptoms", keystone)
        self.assertGreaterEqual(len(keystone["downstream_symptoms"]), 2)
        symptom_text = " ".join(keystone["downstream_symptoms"])
        self.assertIn("ATTRIBUTE_INCOMPLETENESS", symptom_text)
        self.assertIn("CTA_REACHABILITY_FRICTION", symptom_text)

    def test_routes_match_prevents_substring_collisions(self):
        """Topological route matching must not produce false substring collisions on shared character sequences."""
        from causal_gate import routes_match

        # Substring prefix/containment collisions must NOT match
        self.assertFalse(routes_match("/en", "https://example.com/enterprise"))
        self.assertFalse(routes_match("/art", "https://example.com/partners"))
        self.assertFalse(routes_match("/app", "https://example.com/apple"))
        self.assertFalse(routes_match("/en/products/default", "https://example.com/en"))
        self.assertFalse(routes_match("https://example.com/en/products/default", "/en"))
        self.assertFalse(routes_match("https://otherdomain.com/pricing", "https://example.com/pricing"))

        # Valid topological matches must match
        self.assertTrue(routes_match("/en/products/default", "https://example.com/en/products/default"))
        self.assertTrue(routes_match("/en/products/default/", "https://example.com/en/products/default"))
        self.assertTrue(routes_match("/en/products/default?ref=123", "https://example.com/en/products/default"))
        self.assertTrue(routes_match("/en/products/default#reviews", "https://example.com/en/products/default"))
        self.assertTrue(routes_match("https://example.com/pricing", "https://example.com/pricing/"))

    def test_route_level_suppression_preserves_other_routes_and_unscoped_findings(self):
        """A rendering gap on a single product route must NOT suppress findings on other rendered routes or unscoped findings."""
        raw_findings = [
            {
                "id": "F-001",
                "cause_id": "RENDERED_CONTENT_GAP",
                "scope": "https://example.com/en/products/default",
                "severity": "critical",
                "title": "Blank SPA Shell on Product Route",
            },
            {
                "id": "F-002",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "scope": "https://example.com/en/products/default",
                "severity": "high",
                "title": "No Product Schema on Shell Route",
            },
            {
                "id": "F-003",
                "cause_id": "SCHEMA_MISSING",
                "severity": "high",
                "title": "Missing Organization Schema Site-Wide",
            },
            {
                "id": "F-004",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "scope": "https://example.com/en",
                "severity": "medium",
                "title": "Delayed CTA on English Home",
            },
            {
                "id": "F-005",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "scope": "https://example.com/enterprise",
                "severity": "medium",
                "title": "Delayed CTA on Enterprise Page",
            },
        ]
        inv = {
            "pages": [
                {"url": "https://example.com/en", "page_type": "homepage", "word_count": 450, "snr": 0.45},
                {"url": "https://example.com/enterprise", "page_type": "services", "word_count": 600, "snr": 0.5},
                {"url": "https://example.com/en/products/default", "page_type": "product", "word_count": 3, "snr": 0.01},
            ]
        }

        allowed, suppressed, dag_metadata = apply_causal_suppression(raw_findings, inv=inv)
        self.assertFalse(dag_metadata["is_site_wide_rendering_gap"])

        # F-002 on /en/products/default must be suppressed
        suppressed_ids = [f["id"] for f in suppressed]
        self.assertEqual(suppressed_ids, ["F-002"])

        # F-001 (keystone), F-003 (unscoped Org schema), F-004 (/en), F-005 (/enterprise) must ALL survive
        allowed_ids = [f["id"] for f in allowed]
        self.assertIn("F-001", allowed_ids)
        self.assertIn("F-003", allowed_ids)
        self.assertIn("F-004", allowed_ids)
        self.assertIn("F-005", allowed_ids)

    def test_orchestrator_synthesize_report_downstream_symptoms_order_independence(self):
        """Orchestrator must attach downstream symptoms to keystone finding even when keystone has higher severity."""
        from orchestrator import synthesize_audit_report

        raw_findings = [
            {
                "id": "F-KEYSTONE",
                "cause_id": "RENDERED_CONTENT_GAP",
                "scope": "https://example.com/en/products/default",
                "severity": "critical",
                "title": "Blank SPA Shell on Product Route",
                "evidence": "Raw HTML contains 3 words before client-side hydration.",
                "suggested_action": {"summary": "Implement SSR", "priority": "critical"},
            },
            {
                "id": "F-SYMPTOM",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "scope": "https://example.com/en/products/default",
                "severity": "medium",
                "title": "Missing Product Schema",
                "evidence": "Product JSON-LD omitted.",
                "suggested_action": {"summary": "Add Product Schema", "priority": "medium"},
            },
        ]
        inv = {
            "pages": [
                {"url": "https://example.com/", "page_type": "homepage", "word_count": 400, "snr": 0.4},
                {"url": "https://example.com/en/products/default", "page_type": "product", "word_count": 3, "snr": 0.01},
            ]
        }
        report = synthesize_audit_report("https://example.com", inv, {"test": {"findings": raw_findings}})
        self.assertEqual(len(report["findings"]), 1)
        keystone = report["findings"][0]
        self.assertEqual(keystone["cause_id"], "RENDERED_CONTENT_GAP")
        self.assertIn("downstream_symptoms", keystone)
        self.assertEqual(len(keystone["downstream_symptoms"]), 1)
        self.assertIn("ATTRIBUTE_INCOMPLETENESS", keystone["downstream_symptoms"][0])

    def test_assemble_preserves_downstream_symptoms_and_proactive_actions(self):
        """assemble() must preserve downstream symptoms and emit Pre-Hydration Product Schema action."""
        from assemble_report import assemble

        candidates = [
            {
                "check_id": "C1",
                "title": "Blank SPA Shell on Product Route",
                "actual_band": "S3",
                "finding_kind": "confirmed_problem",
                "scope": "https://example.com/en/products/default",
                "cause_id": "RENDERED_CONTENT_GAP",
                "observation": "Only 3 words in initial HTML",
                "evidence_refs": [{"artifact": "r1", "locator": "source.text", "quote": "shell"}],
                "collection_complete_for_scope": True,
                "severity_reason": "SPA unrendered shell",
                "suggested_action": {"summary": "Implement SSR", "priority": "high"},
            },
            {
                "check_id": "E5",
                "title": "Missing Product Schema",
                "actual_band": "S3",
                "finding_kind": "confirmed_problem",
                "scope": "https://example.com/en/products/default",
                "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                "observation": "Missing Product JSON-LD",
                "evidence_refs": [{"artifact": "r1", "locator": "source.text", "quote": "shell"}],
                "collection_complete_for_scope": True,
                "severity_reason": "Missing schema on product route",
                "suggested_action": {"summary": "Add Schema", "priority": "high"},
            },
        ]
        records = [
            {
                "artifact": "r1",
                "url": "https://example.com/en/products/default",
                "text": "shell three words",
                "source": {"text": "shell three words", "canonicals": []},
                "status": 200,
            },
        ]
        checks = [
            {"check_id": "C1", "solution_level": "C", "solution": "Implement SSR"},
            {"check_id": "E5", "solution_level": "C", "solution": "Add Product JSON-LD"},
        ]
        report = assemble("https://example.com", candidates, records, checks, {})

        # The downstream E5 candidate should be suppressed from findings
        finding_check_ids = [f["check_id"] for f in report["findings"]]
        self.assertEqual(finding_check_ids, ["C1"])

        # Keystone C1 finding must have downstream symptoms attached
        c1_finding = report["findings"][0]
        self.assertIn("downstream_symptoms", c1_finding)
        self.assertTrue(any("ATTRIBUTE_INCOMPLETENESS" in s for s in c1_finding["downstream_symptoms"]))

        # Proactive action for pre-hydration schema should be emitted
        proactive_titles = [p["title"] for p in report.get("proactive_actions", [])]
        self.assertIn("Pre-Hydration Product Schema Architecture", proactive_titles)


if __name__ == "__main__":
    unittest.main()
