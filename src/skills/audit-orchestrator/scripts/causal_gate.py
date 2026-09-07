#!/usr/bin/env python3
"""
causal_gate.py - Deterministic Causal DAG & Epistemic Falsification Engine.

Enforces monotonic dependency ordering:
  R0 DNS / Network Reachability
    -> R1 HTTP Retrieval
      -> R2 Robots / Crawl Permission
        -> R3 HTML Readability
          -> R4 Render Completeness
            -> R5 Entity Schema
              -> [R6 Fact Integrity, R7 GEO Citability, External Corroboration]
  R8 Engagement is a sibling branch gated per-URL by R1 HTTP Retrieval.

This module deterministically suppresses impossible downstream findings when
upstream preconditions fail, ensuring zero false positives.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Layer-Specific Root Cause Sets
# ---------------------------------------------------------------------------
LAYER0_CAUSE_IDS: Set[str] = {
    "AI_RETRIEVAL_BLOCKED",
    "NOINDEX_EXCLUSION",
    "ROBOTS_5XX_FAIL_CLOSED",
    "ROBOTS_TXT_OVERSIZED",
    "DNS_UNREACHABLE",
    "HTTP_RETRIEVAL_ZERO",
}

LAYER1_CAUSE_IDS: Set[str] = {
    "RENDERED_CONTENT_GAP",
    "NOSNIPPET_ON_CORE_CONTENT",
    "WAF_BOT_CHALLENGE",
    "CANONICAL_FRAGMENTATION",
    "HTML_EMPTY",
    "JS_REQUIRED",
}

# Findings at Layers 2-5 that are symptoms of Layer 0 access block
SUPPRESSED_BY_LAYER0: Set[str] = {
    # Layer 2 — Entity Resolution
    "MATERIAL_ENTITY_AMBIGUITY",
    "SCHEMA_MISSING",
    "SCHEMA_INVALID",
    "BROKEN_AUTHORITY_ANCHOR",
    "CIRCULAR_SAMEAS_SELF_REFERENCE",
    "WEAK_IDENTITY_SIGNALS",
    # Layer 3 — Fact Ledger
    "FIRST_PARTY_FACT_CONFLICT",
    "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
    "INCOMPLETE_OFFER_ATTRIBUTES",
    "STALE_AUTHORITATIVE_FACT",
    "ATTRIBUTE_INCOMPLETENESS",
    # Layer 4 — Citability & Text Structure
    "MISSING_IN_DEPTH_MECHANISMS",
    "STANDALONE_FAQ_DEFICIT",
    "LOW_FACT_TO_TOKEN_RATIO",
    "EXCESSIVE_KEYWORD_DENSITY",
    "CONTEXT_PLACEMENT_DEGRADATION",
    "LOW_INFORMATION_SCENT",
    "LOW_CITABILITY_SCORE",
    "LACK_OF_SPECIFIC_EVIDENCE",
    # Layer 5 — Engine Selection & Referral Continuity
    "AI_CITATION_GAP",
    "AI_FACT_CONFLICT",
    "AI_REFERRAL_DISCONTINUITY",
    "INTENT_TO_LANDING_MISMATCH",
    "DESTINATION_NAVIGATION_FRICTION",
}

# Findings at Layers 3-4 that are symptoms of Layer 1 unhydrated rendering gap
SUPPRESSED_BY_LAYER1: Set[str] = {
    # Layer 3 — cannot read facts from an unrendered shell
    "FIRST_PARTY_FACT_CONFLICT",
    "INCOMPLETE_OFFER_ATTRIBUTES",
    "ATTRIBUTE_INCOMPLETENESS",
    "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
    # Layer 4 — cannot evaluate citation quality of an empty/unhydrated page
    "LOW_FACT_TO_TOKEN_RATIO",
    "MISSING_IN_DEPTH_MECHANISMS",
    "CONTEXT_PLACEMENT_DEGRADATION",
    "LOW_CITABILITY_SCORE",
    "LACK_OF_SPECIFIC_EVIDENCE",
    "LOW_INFORMATION_SCENT",
}


def evaluate_epistemic_state(
    inv: Optional[Dict[str, Any]] = None,
    specialist_results: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """Derive 7-dimensional epistemic state: 'observed' | 'inferred' | 'unknown' | 'suppressed'."""
    state = {
        "retrieval": "unknown",
        "rendering": "unknown",
        "entity": "unknown",
        "facts": "unknown",
        "corroboration": "unknown",
        "geo": "unknown",
        "engagement": "unknown",
    }

    if not inv:
        return state

    pages = inv.get("pages", [])
    if not pages:
        state["retrieval"] = "unknown"
        for k in ("rendering", "entity", "facts", "corroboration", "geo", "engagement"):
            state[k] = "suppressed"
        return state

    # 1. Retrieval
    any_200 = any(p.get("status") == 200 for p in pages)
    disc_cov = (specialist_results or {}).get("discoverability-audit", {}).get("coverage", {})
    bots_allowed = disc_cov.get("retrieval_bots_allowed", None)

    if any_200 and (bots_allowed is None or bots_allowed > 0):
        state["retrieval"] = "observed"
    elif not any_200:
        state["retrieval"] = "failed"
        for k in ("rendering", "entity", "facts", "corroboration", "geo", "engagement"):
            state[k] = "suppressed"
        return state
    else:
        state["retrieval"] = "blocked"
        for k in ("rendering", "entity", "facts", "corroboration", "geo", "engagement"):
            state[k] = "suppressed"
        return state

    # 2. Rendering
    visible_words = disc_cov.get("visible_words_initial_html", None)
    has_spa_gap = any(p.get("snr", 1.0) < 0.05 and (p.get("word_count", 0) < 30) for p in pages)
    if has_spa_gap or (visible_words is not None and visible_words < 50):
        state["rendering"] = "gap"
        state["geo"] = "suppressed"
        state["facts"] = "suppressed"
    else:
        state["rendering"] = "observed"

    # 3. Entity
    entity_cov = (specialist_results or {}).get("entity-content-audit", {}).get("coverage", {})
    jsonld_present = entity_cov.get("jsonld_present", False)
    if jsonld_present:
        state["entity"] = "observed"
    else:
        state["entity"] = "missing"

    # 4. Facts
    if state["facts"] != "suppressed":
        fact_cov = (specialist_results or {}).get("fact-consistency-audit", {}).get("coverage", {})
        facts_checked = fact_cov.get("facts_checked", 0)
        state["facts"] = "observed" if facts_checked > 0 else "inferred"

    # 5. Corroboration
    corrob_cov = (specialist_results or {}).get("corroboration-authority-audit", {}).get("coverage", {})
    sameas_count = corrob_cov.get("sameas_declared", 0)
    state["corroboration"] = "observed" if sameas_count > 0 else "unsupported"

    # 6. GEO
    if state["geo"] != "suppressed":
        geo_cov = (specialist_results or {}).get("geo-content-audit", {}).get("coverage", {})
        cit_score = geo_cov.get("average_citability_score", None)
        state["geo"] = "observed" if cit_score is not None else "inferred"

    # 7. Engagement
    eng_cov = (specialist_results or {}).get("engagement-context-audit", {}).get("coverage", {})
    pages_eval = eng_cov.get("pages_evaluated", 0)
    state["engagement"] = "observed" if pages_eval > 0 else "inferred"

    return state


def build_evidence_index(
    inv: Dict[str, Any],
    specialist_results: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Index discrete empirical observations with deterministic IDs (EV-001, EV-002, ...)."""
    evidence_index: List[Dict[str, Any]] = []
    counter = 1

    # 1. Robots & Crawlability Evidence
    robots = inv.get("robots", {})
    if robots:
        summary = robots.get("summary", {})
        evidence_index.append({
            "id": f"EV-{counter:03d}",
            "route": "/robots.txt",
            "kind": "robots",
            "observation": f"Robots.txt parsed with rules for {len(summary)} user agent(s).",
        })
        counter += 1

    # 2. Pages & Rendering Evidence
    for p in inv.get("pages", [])[:10]:
        url = p.get("url", "/")
        wc = p.get("word_count", 0)
        snr = round(float(p.get("snr", 0.0)), 2)
        evidence_index.append({
            "id": f"EV-{counter:03d}",
            "route": url,
            "kind": "rendering",
            "observation": f"HTTP {p.get('status', 200)}, visible words: {wc}, SNR: {snr}.",
        })
        counter += 1

    # 3. Entity Evidence
    entity_res = specialist_results.get("entity-content-audit", {})
    types_declared = entity_res.get("coverage", {}).get("types_declared", [])
    if types_declared:
        evidence_index.append({
            "id": f"EV-{counter:03d}",
            "route": "/",
            "kind": "entity",
            "observation": f"Schema.org JSON-LD declared types: {', '.join(types_declared)}.",
        })
        counter += 1

    # 4. Corroboration Probes Evidence
    corrob_res = specialist_results.get("corroboration-authority-audit", {})
    probes = corrob_res.get("coverage", {}).get("probes", [])
    for pr in probes[:5]:
        evidence_index.append({
            "id": f"EV-{counter:03d}",
            "route": pr.get("target_url", "/"),
            "kind": "corroboration",
            "observation": f"Probe to {pr.get('target_url')}: result={pr.get('probe_result')}.",
        })
        counter += 1

    # 5. Fact Ledger Evidence
    fact_res = specialist_results.get("fact-consistency-audit", {})
    conflicts = fact_res.get("coverage", {}).get("fact_conflicts", 0)
    checked = fact_res.get("coverage", {}).get("facts_checked", 0)
    evidence_index.append({
        "id": f"EV-{counter:03d}",
        "route": "site-wide",
        "kind": "facts",
        "observation": f"Cross-page ledger evaluated {checked} facts with {conflicts} verified contradictions.",
    })
    counter += 1

    return evidence_index


def apply_causal_suppression(
    all_raw_findings: List[Dict[str, Any]],
    inv: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Apply the Monotonic Causal DAG suppression rules.

    Returns:
        (allowed_findings, suppressed_findings, dag_metadata)
    """
    has_layer0_block = any(
        (f.get("cause_id") or f.get("id", "")) in LAYER0_CAUSE_IDS
        for f in all_raw_findings
    )
    has_layer1_rendering_gap = any(
        (f.get("cause_id") or f.get("id", "")) in LAYER1_CAUSE_IDS
        for f in all_raw_findings
    )

    allowed: List[Dict[str, Any]] = []
    suppressed: List[Dict[str, Any]] = []
    suppressed_categories: Set[str] = set()
    root_causes: List[Dict[str, Any]] = []

    if has_layer0_block:
        root_causes.append({
            "code": "AI_RETRIEVAL_BLOCKED",
            "scope": "site",
            "suppressed_categories": sorted(list(SUPPRESSED_BY_LAYER0)),
            "rationale": "RFC 9309 search retrieval bot blocked or HTTP 4xx/5xx crawl failure preempts downstream evaluation.",
        })
        suppressed_categories.update(SUPPRESSED_BY_LAYER0)

    if has_layer1_rendering_gap:
        root_causes.append({
            "code": "RENDERED_CONTENT_GAP",
            "scope": "site",
            "suppressed_categories": sorted(list(SUPPRESSED_BY_LAYER1)),
            "rationale": "Static plain text ratio below threshold with unhydrated SPA shell preempts citability and fact evaluation.",
        })
        suppressed_categories.update(SUPPRESSED_BY_LAYER1)

    for f in all_raw_findings:
        cid = f.get("cause_id") or f.get("id") or f.get("title", "")

        if has_layer0_block and cid in SUPPRESSED_BY_LAYER0:
            suppressed.append(f)
            continue
        if has_layer1_rendering_gap and cid in SUPPRESSED_BY_LAYER1:
            suppressed.append(f)
            continue

        allowed.append(f)

    dag_metadata = {
        "has_layer0_block": has_layer0_block,
        "has_layer1_rendering_gap": has_layer1_rendering_gap,
        "root_causes": root_causes,
        "suppressed_categories": sorted(list(suppressed_categories)),
    }

    return allowed, suppressed, dag_metadata
