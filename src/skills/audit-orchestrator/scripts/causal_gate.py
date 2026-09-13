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
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# Bidirectional Taxonomy Alias Mapping between Synthesis Keys and Sensor Output Keys
TAXONOMY_ALIASES: Dict[str, str] = {
    "META_DIRECTIVE_CONFLICT": "NOINDEX_EXCLUSION",
    "NOINDEX_EXCLUSION": "META_DIRECTIVE_CONFLICT",
    "CANONICAL_TARGET_MISMATCH": "CANONICAL_FRAGMENTATION",
    "CANONICAL_FRAGMENTATION": "CANONICAL_TARGET_MISMATCH",
    "UNVERIFIED_AUTHORITY_GAP": "WEAK_IDENTITY_SIGNALS",
    "WEAK_IDENTITY_SIGNALS": "UNVERIFIED_AUTHORITY_GAP",
    "SUB_THRESHOLD_CITABILITY": "LOW_CITABILITY_SCORE",
    "LOW_CITABILITY_SCORE": "SUB_THRESHOLD_CITABILITY",
    "MISSING_BLUF_PRIMACY": "CONTEXT_PLACEMENT_DEGRADATION",
    "CONTEXT_PLACEMENT_DEGRADATION": "MISSING_BLUF_PRIMACY",
    "INTENT_SCENT_DILUTION": "LOW_INFORMATION_SCENT",
    "LOW_INFORMATION_SCENT": "INTENT_SCENT_DILUTION",
    "COMMERCIAL_HANDOFF_DISCONTINUITY": "INTENT_TO_LANDING_MISMATCH",
    "INTENT_TO_LANDING_MISMATCH": "COMMERCIAL_HANDOFF_DISCONTINUITY",
    "ABOVE_FOLD_ACTION_DELAY": "CTA_REACHABILITY_FRICTION",
    "CTA_REACHABILITY_FRICTION": "ABOVE_FOLD_ACTION_DELAY",
    "DELAYED_COMMERCIAL_CALL_TO_ACTION": "CTA_REACHABILITY_FRICTION",
    "INERT_CTA_TARGET": "CTA_REACHABILITY_FRICTION",
    "TEMPORAL_DRIFT_DETECTED": "CONTENT_RECENCY_DEFICIT",
    "CONTENT_RECENCY_DEFICIT": "TEMPORAL_DRIFT_DETECTED",
    "ROBOTS_SITEWIDE_DISALLOW": "AI_RETRIEVAL_BLOCKED",
}

# ---------------------------------------------------------------------------
# Layer-Specific Root Cause Sets
# ---------------------------------------------------------------------------
LAYER0_CAUSE_IDS: Set[str] = {
    "AI_RETRIEVAL_BLOCKED",
    "ROBOTS_SITEWIDE_DISALLOW",
    "NOINDEX_EXCLUSION",
    "META_DIRECTIVE_CONFLICT",
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
    "CANONICAL_TARGET_MISMATCH",
    "HTML_EMPTY",
    "JS_REQUIRED",
}

# Findings at Layers 2-5 that are symptoms of Layer 0 access block
SUPPRESSED_BY_LAYER0: Set[str] = {
    # Layer 1 — Rendering (cannot evaluate client rendering if access is blocked)
    "RENDERED_CONTENT_GAP",
    "NOSNIPPET_ON_CORE_CONTENT",
    "JS_REQUIRED",
    "HTML_EMPTY",
    # Layer 2 — Entity Resolution
    "MATERIAL_ENTITY_AMBIGUITY",
    "MISSING_SAMEAS_VERIFICATION",
    "UNLINKED_KNOWLEDGE_GRAPH_ANCHOR",
    "CLAIM_CORROBORATION_GAP",
    "SCHEMA_MISSING",
    "SCHEMA_INVALID",
    "BROKEN_AUTHORITY_ANCHOR",
    "CIRCULAR_SAMEAS_SELF_REFERENCE",
    "WEAK_IDENTITY_SIGNALS",
    "UNVERIFIED_AUTHORITY_GAP",
    # Layer 3 — Fact Ledger
    "FIRST_PARTY_FACT_CONFLICT",
    "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
    "CONFLICTING_COMMERCIAL_TERMS",
    "DISCONTINUED_VS_CURRENT_CONFLICT",
    "INCOMPLETE_OFFER_ATTRIBUTES",
    "STALE_AUTHORITATIVE_FACT",
    "ATTRIBUTE_INCOMPLETENESS",
    "CONTENT_RECENCY_DEFICIT",
    "TEMPORAL_DRIFT_DETECTED",
    # Layer 4 — Citability & Text Structure
    "MISSING_IN_DEPTH_MECHANISMS",
    "STANDALONE_FAQ_DEFICIT",
    "LOW_FACT_TO_TOKEN_RATIO",
    "EXCESSIVE_KEYWORD_DENSITY",
    "EXCESSIVE_HEDGE_LANGUAGE",
    "LOCALE_MISCONFIGURATION",
    "COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT",
    "CONTEXT_PLACEMENT_DEGRADATION",
    "MISSING_BLUF_PRIMACY",
    "LOW_INFORMATION_SCENT",
    "INTENT_SCENT_DILUTION",
    "LOW_CITABILITY_SCORE",
    "SUB_THRESHOLD_CITABILITY",
    "LACK_OF_SPECIFIC_EVIDENCE",
    "VIEWPORT_ANSWER_ABSENCE",
    "GENERIC_H1",
    "HEADING_HIERARCHY_VACUUM",
    "INFORMATION_GAIN_DEFICIT",
    "PRIMARY_AUTHORITY_QUOTATION_GAP",
    "COMPARATIVE_ANSWERABILITY_MATRIX",
    # Layer 5 & 6 — Engine Selection, Trust & Referral Continuity
    "AI_CITATION_GAP",
    "AI_FACT_CONFLICT",
    "AI_REFERRAL_DISCONTINUITY",
    "INTENT_TO_LANDING_MISMATCH",
    "COMMERCIAL_HANDOFF_DISCONTINUITY",
    "CTA_REACHABILITY_FRICTION",
    "ABOVE_FOLD_ACTION_DELAY",
    "DESTINATION_NAVIGATION_FRICTION",
    "VALUE_PROPOSITION_ORIENTATION_VACUUM",
    "PROOF_ARCHITECTURE_DEFICIT",
    "FRICTION_TO_VALUE_BARRIER",
    "OBJECTION_COVERAGE_VOID",
    "DECISION_PATHWAY_DEAD_END",
}

# Findings at Layers 2-6 that are downstream symptoms of Layer 1 unhydrated rendering gap
SUPPRESSED_BY_LAYER1: Set[str] = {
    # Layer 2 — Entity & Answerability (Product/Catalog routes cannot resolve schema without hydration)
    "ATTRIBUTE_INCOMPLETENESS",
    "INCOMPLETE_OFFER_ATTRIBUTES",
    "SCHEMA_MISSING",
    "SCHEMA_INVALID",
    "MISSING_MATERIAL_FACT",
    "CLAIM_CORROBORATION_GAP",
    # Layer 3 — Fact Ledger (cannot read facts from an unrendered shell)
    "FIRST_PARTY_FACT_CONFLICT",
    "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
    "CONFLICTING_COMMERCIAL_TERMS",
    "DISCONTINUED_VS_CURRENT_CONFLICT",
    "CONTENT_RECENCY_DEFICIT",
    "TEMPORAL_DRIFT_DETECTED",
    "STALE_AUTHORITATIVE_FACT",
    # Layer 4 — Citability & Text Structure (cannot evaluate citation quality of an empty/unhydrated page)
    "LOW_FACT_TO_TOKEN_RATIO",
    "MISSING_IN_DEPTH_MECHANISMS",
    "COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT",
    "CONTEXT_PLACEMENT_DEGRADATION",
    "MISSING_BLUF_PRIMACY",
    "LOW_CITABILITY_SCORE",
    "SUB_THRESHOLD_CITABILITY",
    "LACK_OF_SPECIFIC_EVIDENCE",
    "LOW_INFORMATION_SCENT",
    "INTENT_SCENT_DILUTION",
    "STANDALONE_FAQ_DEFICIT",
    "EXCESSIVE_KEYWORD_DENSITY",
    "EXCESSIVE_HEDGE_LANGUAGE",
    "LOCALE_MISCONFIGURATION",
    "INFORMATION_GAIN_DEFICIT",
    "PRIMARY_AUTHORITY_QUOTATION_GAP",
    "COMPARATIVE_ANSWERABILITY_MATRIX",
    # Layer 5 & 6 — Engagement, Orientation & Referral Continuity (cannot measure CTAs or headings on unrendered DOM)
    "CTA_REACHABILITY_FRICTION",
    "ABOVE_FOLD_ACTION_DELAY",
    "DELAYED_COMMERCIAL_CALL_TO_ACTION",
    "INERT_CTA_TARGET",
    "VIEWPORT_ANSWER_ABSENCE",
    "AGENT_INTERACTION_BARRIER",
    "INTENT_TO_LANDING_MISMATCH",
    "COMMERCIAL_HANDOFF_DISCONTINUITY",
    "DESTINATION_NAVIGATION_FRICTION",
    "AI_REFERRAL_DISCONTINUITY",
    "GENERIC_H1",
    "HEADING_HIERARCHY_VACUUM",
    "VALUE_PROPOSITION_ORIENTATION_VACUUM",
    "PROOF_ARCHITECTURE_DEFICIT",
    "FRICTION_TO_VALUE_BARRIER",
    "OBJECTION_COVERAGE_VOID",
    "DECISION_PATHWAY_DEAD_END",
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
    has_spa_gap = any(
        float(p.get("snr") or 1.0) < 0.05 and int(p.get("word_count") or 0) < 30
        for p in pages
        if isinstance(p, dict)
    )
    if has_spa_gap or (isinstance(visible_words, (int, float)) and visible_words < 50):
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
        wc = int(p.get("word_count") or 0)
        snr = round(float(p.get("snr") or 0.0), 2)
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


def extract_finding_route(f: Dict[str, Any]) -> str:
    """Extract and normalize route / URL from finding dict."""
    if not isinstance(f, dict):
        return ""
    # 1. Direct url property
    url = f.get("url")
    if isinstance(url, dict):
        url = url.get("url") or url.get("scope") or ""

    # 2. Check scope if it looks like a URL or route path
    scope = f.get("scope")
    if isinstance(scope, dict):
        scope = scope.get("url") or scope.get("scope") or ""
    scope_str = str(scope or "").strip()
    if not url and scope_str and (scope_str.startswith(("/", "http://", "https://", "//")) or "." in scope_str.split("/")[0]):
        url = scope_str

    # 3. Check evidence sources
    ev = f.get("evidence")
    if not url and isinstance(ev, dict):
        sources = ev.get("sources", [])
        if isinstance(sources, list) and sources:
            for s in sources:
                if isinstance(s, dict) and s.get("url"):
                    url = s["url"]
                    break
        if not url and ev.get("scope"):
            ev_scope = str(ev["scope"]).strip()
            if ev_scope.startswith(("/", "http://", "https://", "//")):
                url = ev_scope

    # 4. Check evidence string or dict summary regex
    if not url and isinstance(ev, (str, dict)):
        ev_text = json.dumps(ev) if isinstance(ev, dict) else str(ev)
        m = re.search(r'https?://[^\s,\(\)\]"\']+', ev_text)
        if m:
            url = m.group(0)

    # 5. Check root cause
    if not url:
        rc = str(f.get("root_cause") or "")
        m = re.search(r'https?://[^\s,\(\)\]"\']+', rc)
        if m:
            url = m.group(0)

    # Fallback to scope string if non-empty
    if not url and scope_str:
        url = scope_str

    return str(url or "").strip().lower()


def normalize_route_path(route: str) -> str:
    """Extract normalized path from URL or route string."""
    if not route:
        return ""
    r = route.strip().lower()
    if "://" not in r and not r.startswith("//") and not r.startswith("/"):
        r = "//" + r
    parsed = urlparse(r)
    path = parsed.path.rstrip("/")
    return path if path else "/"


def routes_match(r1: str, r2: str) -> bool:
    """Check if two route/URL references match topologically without substring collision."""
    if not r1 or not r2:
        return False
    r1_norm = r1.strip().lower()
    r2_norm = r2.strip().lower()
    if r1_norm == r2_norm:
        return True

    # Validate domain conflict if both specify network location
    parsed1 = urlparse(r1_norm if "://" in r1_norm or r1_norm.startswith("//") else "//" + r1_norm)
    parsed2 = urlparse(r2_norm if "://" in r2_norm or r2_norm.startswith("//") else "//" + r2_norm)
    if parsed1.netloc and parsed2.netloc and parsed1.netloc != parsed2.netloc:
        return False

    p1 = normalize_route_path(r1)
    p2 = normalize_route_path(r2)
    if not p1 or not p2:
        return False
    return p1 == p2


def apply_causal_suppression(
    all_raw_findings: List[Dict[str, Any]],
    inv: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Apply the Monotonic 6-Layer Causal DAG suppression rules with route-level precision.

    Returns:
        (allowed_findings, suppressed_findings, dag_metadata)
    """
    def _extract_cids(f: Dict[str, Any]) -> Set[str]:
        cids = {f.get(k) for k in ("cause_id", "id", "code", "root_cause_key", "check_id") if f.get(k)}
        cids.update({TAXONOMY_ALIASES[c] for c in list(cids) if c in TAXONOMY_ALIASES})
        return cids

    layer0_findings = [f for f in all_raw_findings if bool(_extract_cids(f).intersection(LAYER0_CAUSE_IDS))]
    has_layer0_block = bool(layer0_findings)

    layer1_findings = [f for f in all_raw_findings if bool(_extract_cids(f).intersection(LAYER1_CAUSE_IDS))]
    has_layer1_rendering_gap = bool(layer1_findings)

    # Inspect inventory pages directly if available
    inv_pages = inv.get("pages", []) if isinstance(inv, dict) else []
    rendering_gap_pages: Set[str] = set()
    for f in layer1_findings:
        rt = extract_finding_route(f)
        if rt:
            rendering_gap_pages.add(rt)
        for u in f.get("affected_urls", []):
            if u:
                rendering_gap_pages.add(str(u).strip().lower())
        ev_str = str(f.get("evidence", ""))
        for u in re.findall(r'https?://[^\s,\(\)\]"\']+', ev_str):
            rendering_gap_pages.add(u.lower())

    for p in inv_pages:
        if isinstance(p, dict):
            p_url = str(p.get("url", "")).strip().lower()
            wc = int(p.get("word_count") or 0)
            snr = float(p["snr"]) if p.get("snr") is not None else 1.0
            html = str(p.get("html", "")).lower()
            # High-confidence SPA shell detection requiring structural markers OR ultra-thin content (<25 words)
            has_spa_marker = (
                any(m in html for m in ('id="root"', 'id="app"', '@dropins', 'storefront-', 'scripts/aem.js', '__next', 'nuxt'))
                or ('type="module"' in html and wc < 30)
                or '<noscript>' in html
            )
            if p_url and ((wc < 25 and has_spa_marker) or (snr < 0.03 and wc > 0 and wc < 30)):
                rendering_gap_pages.add(p_url)

    has_any_finding_scope = any(bool(extract_finding_route(f)) for f in all_raw_findings)

    is_site_wide_l0 = False
    if has_layer0_block:
        for f in layer0_findings:
            f_rt = extract_finding_route(f)
            f_ev = str(f.get("evidence", "")).lower()
            f_rc = str(f.get("root_cause", "")).lower()
            cid_set = _extract_cids(f)
            if any(c in cid_set for c in ("ROBOTS_5XX_FAIL_CLOSED", "ROBOTS_TXT_OVERSIZED", "DNS_UNREACHABLE", "HTTP_RETRIEVAL_ZERO", "ROBOTS_SITEWIDE_DISALLOW")):
                is_site_wide_l0 = True
                break
            if "AI_RETRIEVAL_BLOCKED" in cid_set:
                has_route_subpath = any(sub in f_ev for sub in ("/blog", "/admin", "/cart", "/checkout", "/api", "/content", "/quiz", "/product", "/item", "/news")) or (f_rt and normalize_route_path(f_rt) != "/")
                if not has_route_subpath and (normalize_route_path(f_rt) == "/" or f_rt in ("site", "site-wide", "sitewide", "") or "root" in f_ev or "root url" in str(f.get("title", "")).lower() or "403" in f_ev or not inv_pages):
                    is_site_wide_l0 = True
                    break
            if f_rt in ("site", "site-wide", "sitewide") or "sitewide" in f_ev or "disallows all" in f_rc:
                is_site_wide_l0 = True
                break
            if re.search(r"disallow:\s*/(?:\s|$)", f_ev):
                is_site_wide_l0 = True
                break
            if cid_set.intersection({"NOINDEX_EXCLUSION", "META_DIRECTIVE_CONFLICT"}) and (
                "sitewide" in f_ev or "homepage" in f_ev or f_rt in ("/", "", "site", "site-wide", "sitewide") or normalize_route_path(f_rt) == "/"
            ):
                is_site_wide_l0 = True
                break
            if not has_any_finding_scope and not f_rt and not any(sub in f_ev for sub in ("/blog", "/admin", "/cart", "/checkout", "/api", "/content", "/quiz", "/product")):
                is_site_wide_l0 = True
                break

    is_site_wide_rendering_gap = False
    if has_layer1_rendering_gap:
        if not has_any_finding_scope:
            is_site_wide_rendering_gap = True
        else:
            # Site-wide rendering gap requires explicit site-wide declaration or confirmed universal failure across all crawled HTML pages
            html_pages = [p for p in inv_pages if isinstance(p, dict) and p.get("html")]
            all_pages_unrendered = len(html_pages) >= 3 and all(str(p.get("url", "")).strip().lower() in rendering_gap_pages for p in html_pages)
            if all_pages_unrendered:
                is_site_wide_rendering_gap = True
            else:
                for f in layer1_findings:
                    f_rt = extract_finding_route(f)
                    f_ev = str(f.get("evidence", "")).lower()
                    if f_rt in ("site", "site-wide", "sitewide") or "sitewide" in f_ev:
                        is_site_wide_rendering_gap = True
                        break

    allowed: List[Dict[str, Any]] = []
    suppressed: List[Dict[str, Any]] = []
    suppressed_categories: Set[str] = set()
    root_causes: List[Dict[str, Any]] = []
    downstream_symptoms_by_cause: Dict[str, List[str]] = {}

    if has_layer0_block:
        root_causes.append({
            "code": "AI_RETRIEVAL_BLOCKED",
            "scope": "site" if is_site_wide_l0 else "route",
            "suppressed_categories": sorted(list(SUPPRESSED_BY_LAYER0)),
            "rationale": "RFC 9309 search retrieval bot blocked or HTTP 4xx/5xx crawl failure preempts downstream evaluation.",
        })
        suppressed_categories.update(SUPPRESSED_BY_LAYER0)

    if has_layer1_rendering_gap or rendering_gap_pages:
        root_causes.append({
            "code": "RENDERED_CONTENT_GAP",
            "scope": "site" if is_site_wide_rendering_gap else "route",
            "suppressed_categories": sorted(list(SUPPRESSED_BY_LAYER1)),
            "rationale": "Static plain text ratio below threshold with unhydrated SPA shell preempts citability, facts, and unhydrated engagement.",
        })
        suppressed_categories.update(SUPPRESSED_BY_LAYER1)

    for f in all_raw_findings:
        cids = _extract_cids(f)
        if not cids and f.get("title"):
            cids.add(f["title"])

        f_route = extract_finding_route(f)

        # Evaluate Layer 0 suppression
        suppress_l0 = False
        if has_layer0_block and bool(cids.intersection(SUPPRESSED_BY_LAYER0)) and (
            is_site_wide_l0 or (f_route and any(routes_match(f_route, extract_finding_route(l0_f)) for l0_f in layer0_findings if extract_finding_route(l0_f)))
        ):
            suppress_l0 = True

        if suppress_l0:
            suppressed.append(f)
            primary_l0 = layer0_findings[0].get("cause_id") or "AI_RETRIEVAL_BLOCKED"
            sym_cid0 = f.get("cause_id") or (f.get("id") if f.get("id") and not f.get("id", "").startswith("F-") else None) or next((c for c in cids if not c.startswith("F-")), list(cids)[0] if cids else "DEFECT")
            symptom_label = f"{sym_cid0}: {f.get('title', '')}" + (f" on {f_route}" if f_route else "")
            downstream_symptoms_by_cause.setdefault(primary_l0, []).append(symptom_label)
            continue

        # Evaluate Layer 1 rendering gap suppression with route-level pruning
        suppress_l1 = False
        if bool(cids.intersection(SUPPRESSED_BY_LAYER1)):
            aff_urls = f.get("affected_urls")
            if isinstance(aff_urls, list) and aff_urls and rendering_gap_pages:
                unrendered_on_f = [u for u in aff_urls if any(routes_match(str(u), gap_p) for gap_p in rendering_gap_pages)]
                if unrendered_on_f:
                    remaining_urls = [u for u in aff_urls if not any(routes_match(str(u), gap_p) for gap_p in rendering_gap_pages)]
                    if not remaining_urls or is_site_wide_rendering_gap:
                        suppress_l1 = True
                    else:
                        # Prune unrendered routes from finding and record as downstream symptom
                        f_copy = dict(f)
                        f_copy["affected_urls"] = remaining_urls
                        if f_route and any(routes_match(f_route, gap_p) for gap_p in rendering_gap_pages):
                            f_copy["scope"] = remaining_urls[0]
                        f = f_copy
                        primary_l1 = layer1_findings[0].get("cause_id") or "RENDERED_CONTENT_GAP" if layer1_findings else "RENDERED_CONTENT_GAP"
                        sym_cid1 = f.get("cause_id") or next((c for c in cids if not c.startswith("F-")), "DEFECT")
                        symptom_label = f"{sym_cid1}: {f.get('title', '')} (pruned unrendered routes: {', '.join(unrendered_on_f)})"
                        downstream_symptoms_by_cause.setdefault(primary_l1, []).append(symptom_label)
            elif is_site_wide_rendering_gap or (f_route and any(routes_match(f_route, gap_p) for gap_p in rendering_gap_pages)):
                suppress_l1 = True

        if suppress_l1:
            suppressed.append(f)
            primary_l1 = layer1_findings[0].get("cause_id") or "RENDERED_CONTENT_GAP" if layer1_findings else "RENDERED_CONTENT_GAP"
            sym_cid1 = f.get("cause_id") or (f.get("id") if f.get("id") and not f.get("id", "").startswith("F-") else None) or next((c for c in cids if not c.startswith("F-")), list(cids)[0] if cids else "DEFECT")
            symptom_label = f"{sym_cid1}: {f.get('title', '')}" + (f" on {f_route}" if f_route else "")
            downstream_symptoms_by_cause.setdefault(primary_l1, []).append(symptom_label)
            continue

        allowed.append(f)

    # Attach downstream symptoms to keystone findings in allowed
    for f in allowed:
        f_cids = _extract_cids(f)
        for cause_key, symptoms in downstream_symptoms_by_cause.items():
            is_l1 = (cause_key in LAYER1_CAUSE_IDS or cause_key == "RENDERED_CONTENT_GAP") and bool(f_cids.intersection(LAYER1_CAUSE_IDS))
            is_l0 = (cause_key in LAYER0_CAUSE_IDS or cause_key == "AI_RETRIEVAL_BLOCKED") and bool(f_cids.intersection(LAYER0_CAUSE_IDS))
            if cause_key in f_cids or TAXONOMY_ALIASES.get(cause_key, "") in f_cids or is_l1 or is_l0:
                f_symptoms = f.setdefault("downstream_symptoms", [])
                for s in symptoms:
                    if s not in f_symptoms:
                        f_symptoms.append(s)

    dag_metadata = {
        "has_layer0_block": has_layer0_block,
        "has_layer1_rendering_gap": has_layer1_rendering_gap,
        "is_site_wide_rendering_gap": is_site_wide_rendering_gap,
        "rendering_gap_pages": sorted(list(rendering_gap_pages)),
        "root_causes": root_causes,
        "suppressed_categories": sorted(list(suppressed_categories)),
        "downstream_symptoms": downstream_symptoms_by_cause,
    }

    return allowed, suppressed, dag_metadata


# ---------------------------------------------------------------------------
# Section 2 & 5 Mathematical Formulas & Epistemic Constants
# ---------------------------------------------------------------------------

DEFAULT_LIMITATIONS: List[str] = [
    "No JavaScript browser rendering was performed.",
    "Robots eligibility was simulated from the captured robots.txt; bot-specific server responses were not tested.",
    "No external analytics were supplied, so engagement findings are content and navigation proxies rather than observed bounce rates.",
    "No claim is made about actual citation by any specific AI assistant.",
]

ROOT_CAUSE_PRECEDENCE: List[str] = [
    "SITE_UNAVAILABLE_OR_BLOCKED",
    "AI_RETRIEVAL_BLOCKED",
    "INDEXING_DISABLED",
    "CLIENT_RENDERING_DEPENDENCY",
    "ENTITY_AMBIGUITY",
    "FACT_CONTRADICTION",
    "LOW_CITABILITY",
    "ENGAGEMENT_HANDOFF_FRICTION",
]


def compute_severity_score(
    confidence: float,
    causal_reach: float,
    affected_coverage: float,
    user_value_loss: float,
    remediation_leverage: float,
) -> float:
    """Calculate empirical severity score [0, 100] per Section 2 Severity Formula.

    score = 100 * confidence * (
        0.35 * causal_reach +
        0.30 * affected_coverage +
        0.20 * user_value_loss +
        0.15 * remediation_leverage
    )
    """
    conf = max(0.0, min(1.0, confidence))
    cr = max(0.0, min(1.0, causal_reach))
    ac = max(0.0, min(1.0, affected_coverage))
    uv = max(0.0, min(1.0, user_value_loss))
    rl = max(0.0, min(1.0, remediation_leverage))
    return round(100.0 * conf * (0.35 * cr + 0.30 * ac + 0.20 * uv + 0.15 * rl), 2)


def severity_from_score(score: float) -> str:
    """Map numeric severity score to Draft-07 compliant severity category."""
    if score >= 85.0:
        return "critical"
    elif score >= 65.0:
        return "high"
    elif score >= 40.0:
        return "medium"
    return "low"


def compute_archetype_confidence(
    route_signal_strength: float,
    vocabulary_signal_strength: float,
    structured_data_signal_strength: float,
    commercial_or_editorial_signal_strength: float,
) -> float:
    """Calculate archetype confidence [0, 1] per Section 5 Archetype Formula.

    archetype_confidence = (
        0.40 * route_signal_strength +
        0.25 * vocabulary_signal_strength +
        0.20 * structured_data_signal_strength +
        0.15 * commercial_or_editorial_signal_strength
    )
    """
    rs = max(0.0, min(1.0, route_signal_strength))
    vs = max(0.0, min(1.0, vocabulary_signal_strength))
    sd = max(0.0, min(1.0, structured_data_signal_strength))
    ce = max(0.0, min(1.0, commercial_or_editorial_signal_strength))
    return round(0.40 * rs + 0.25 * vs + 0.20 * sd + 0.15 * ce, 4)


def detect_business_archetype(inv: Dict[str, Any]) -> str:
    """Classifies website into primary business archetype from crawl inventory."""
    if not inv or not isinstance(inv, dict):
        return "corporate"

    # Explicit archetype in inventory if declared and valid
    explicit_arch = inv.get("archetype") or (inv.get("metadata", {}).get("archetype") if isinstance(inv.get("metadata"), dict) else None)
    if explicit_arch in ("ecommerce", "saas", "publisher", "local_business", "corporate"):
        return explicit_arch

    pages = inv.get("pages", []) if inv else []
    if not pages:
        return "corporate"

    ecomm_score = 0
    saas_score = 0
    publisher_score = 0
    local_score = 0

    for p in pages:
        if not isinstance(p, dict):
            continue
        ptype = (p.get("page_type") or "")
        if isinstance(ptype, dict):
            ptype = str(ptype.get("value", "")).lower()
        else:
            ptype = str(ptype).lower()

        url = (p.get("url") or "").lower()
        text = (p.get("clean_text") or p.get("clean_markdown") or "").lower()
        title_val = p.get("title")
        if isinstance(title_val, list):
            title = (title_val[0] if title_val else "").lower()
        else:
            title = (title_val or "").lower()

        h1_val = p.get("h1")
        if isinstance(h1_val, list):
            h1 = (h1_val[0] if h1_val else "").lower()
        else:
            h1 = (h1_val or "").lower()

        jld_str = json.dumps(p.get("jsonld", []) or p.get("json_ld_contents", []) or []).lower()
        visible_text = f"{text} {title} {h1}".lower()

        # 1. Ecommerce (Retail, consumer products, shopping carts, subscriptions)
        if ptype in ("product_detail", "product", "product_listing", "category", "cart", "checkout", "subscription_flow") or any(
            k in url for k in (
                "/product", "/products", "/shop", "/item", "/items", "/store",
                "/collection", "/collections", "/catalog", "/catalogue", "/cart",
                "/checkout", "/goods", "/merchandise", "/coffee", "/subscription",
                "/beans", "/roast"
            )
        ):
            ecomm_score += 3
        if any(k in visible_text for k in (
            "add to cart", "shopping cart", "free shipping", "envío gratis",
            "in stock", "out of stock", "shipping & returns", "item in stock",
            "add to basket", "buy now", "order summary", "item total",
            "pickup & delivery", "same day delivery", "order pickup",
            "weekly ad", "registry & wish list", "delivered to your door",
            "first month half-price", "monthly delivery", "subscribe to",
            "whole bean", "ground coffee", "artisan roast", "shop coffee"
        )):
            ecomm_score += 3
        elif any(k in jld_str for k in ("schema.org/product", "schema.org/offer", '"@type": "product"')):
            ecomm_score += 2

        # 2. SaaS & Developer Platforms (Cloud services, subscription software, APIs)
        if ptype in ("pricing", "subscription_flow", "documentation") or any(
            k in url for k in (
                "/pricing", "/plans", "/docs", "/api", "/billing", "/features",
                "/integrations", "/developers", "/solutions", "/platform",
                "/demo", "/contact-sales", "/request-demo", "/product-tour"
            )
        ):
            saas_score += 3
        if any(k in visible_text for k in (
            "per user", "per seat", "api docs", "rest api", "free tier",
            "enterprise plan", "monthly billing", "annual billing", "developer platform",
            "cloud platform", "git repository", "start free trial", "request demo",
            "watch demo", "request a demo", "work platform", "productivity tools",
            "ci/cd", "source code management", "devops", "contact sales"
        )) or any(k in jld_str for k in ("softwareapplication", '"@type": "softwareapplication"')):
            saas_score += 3
        elif any(k in visible_text for k in ("pricing", "plans", "documentation", "plugins", "sdk", "workspace")):
            saas_score += 1

        # 3. Publisher & Editorial (News wires, media, articles, journalism, blogs)
        if ptype in ("article", "blog", "news") or any(
            k in url for k in (
                "/blog", "/news", "/article", "/articles", "/posts/", "/journal",
                "/story", "/stories", "/world", "/tech", "/tag/", "/tags/", "/opinion",
                "/editorial", "/culture", "/entertainment"
            )
        ):
            publisher_score += 3
        if any(k in visible_text for k in (
            "headline", "byline", "author:", "editor:", "published on", "breaking news",
            "top stories", "latest news", "journalism", "broadcasting", "press release", "news wire"
        )) or any(k in jld_str for k in ("newsarticle", "blogposting", '"@type": "article"', '"@type": "newsarticle"')):
            publisher_score += 3

        # 4. Local Business (Physical storefronts, branches, local service providers)
        # Require physical location routes or explicit LocalBusiness schema.
        # Corporate headquarters PostalAddress in footers must NEVER trigger local business!
        if ptype in ("store_locator", "branches", "local_business") or any(
            k in url for k in ("/store-locator", "/our-stores", "/branches", "/find-a-store", "/find-stores")
        ):
            local_score += 4
        elif any(k in url for k in ("/locations", "/location")):
            local_score += 1

        if "localbusiness" in jld_str or '"@type": "localbusiness"' in jld_str:
            local_score += 4
        elif "openinghours" in visible_text and any(k in visible_text for k in ("store hours", "branch", "visit our store", "menu")):
            local_score += 2

    # Publisher precedence: If editorial/news/article signals are prominent
    if publisher_score >= 3 and publisher_score >= saas_score and publisher_score >= ecomm_score:
        return "publisher"

    # SaaS precedence: If strong developer/API/pricing signals exist, classify as SaaS over retail ecomm
    if saas_score >= 3 and saas_score >= ecomm_score:
        return "saas"

    # Ecommerce precedence: If explicit cart/retail transactional signals exist
    if ecomm_score >= 3 and ecomm_score > saas_score and ecomm_score >= local_score:
        return "ecommerce"

    candidates = [
        (publisher_score, "publisher"),
        (saas_score, "saas"),
        (ecomm_score, "ecommerce"),
        (local_score, "local_business"),
    ]
    candidates.sort(key=lambda x: x[0], reverse=True)
    if candidates[0][0] >= 3:
        return candidates[0][1]
    return "corporate"


def evaluate_causal_nodes(
    inv: Optional[Dict[str, Any]] = None,
    specialist_results: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """Evaluate 8 core Causal DAG nodes into the four epistemic states:
    confirmed_pass | confirmed_fail | unknown | not_applicable
    """
    nodes: Dict[str, str] = {
        "reachability": "unknown",
        "retrieval_access": "unknown",
        "static_readability": "unknown",
        "entity_explicitness": "unknown",
        "fact_consistency": "unknown",
        "citability": "unknown",
        "on_site_orientation": "unknown",
        "engagement_handoff": "unknown",
    }

    if not inv:
        return nodes

    pages = inv.get("pages", [])
    if not pages:
        nodes["reachability"] = "confirmed_fail"
        nodes["retrieval_access"] = "confirmed_fail"
        return nodes

    # Reachability & Retrieval
    status_codes = [p.get("status") for p in pages if isinstance(p, dict) and p.get("status") is not None]
    if any(s == 200 for s in status_codes):
        nodes["reachability"] = "confirmed_pass"
    elif status_codes:
        nodes["reachability"] = "confirmed_fail"
        nodes["retrieval_access"] = "confirmed_fail"
        return nodes

    disc_cov = ((specialist_results or {}).get("discoverability-audit") or {}).get("coverage") or {}
    bots_allowed = disc_cov.get("retrieval_bots_allowed")
    if bots_allowed is not None:
        nodes["retrieval_access"] = "confirmed_pass" if bots_allowed > 0 else "confirmed_fail"
    else:
        nodes["retrieval_access"] = "confirmed_pass"

    # Static Readability
    has_spa_shell = any(
        float(p.get("snr") or 1.0) < 0.05 and int(p.get("word_count") or 0) < 30
        for p in pages
        if isinstance(p, dict)
    )
    nodes["static_readability"] = "confirmed_fail" if has_spa_shell else "confirmed_pass"

    # Entity Explicitness
    entity_cov = (specialist_results or {}).get("entity-content-audit", {}).get("coverage", {})
    jsonld_present = entity_cov.get("jsonld_present", False)
    nodes["entity_explicitness"] = "confirmed_pass" if jsonld_present else "confirmed_fail"

    # Fact Consistency
    fact_cov = (specialist_results or {}).get("fact-consistency-audit", {}).get("coverage", {})
    conflicts = fact_cov.get("fact_conflicts", 0)
    checked = fact_cov.get("facts_checked", 0)
    if checked > 0:
        nodes["fact_consistency"] = "confirmed_fail" if conflicts > 0 else "confirmed_pass"
    else:
        nodes["fact_consistency"] = "unknown"

    # Citability
    geo_cov = (specialist_results or {}).get("geo-content-audit", {}).get("coverage", {})
    cit_score = geo_cov.get("average_citability_score")
    if cit_score is not None:
        nodes["citability"] = "confirmed_pass" if cit_score >= 50.0 else "confirmed_fail"
    else:
        nodes["citability"] = "unknown"

    # Orientation & Engagement
    eng_res = (specialist_results or {}).get("engagement-context-audit", {})
    eng_cov = eng_res.get("coverage", {})
    pages_eval = eng_cov.get("pages_evaluated", 0)
    if pages_eval > 0:
        eng_findings = eng_res.get("findings", [])
        finding_ids = set()
        for f in eng_findings:
            if isinstance(f, dict):
                for key in ("cause_id", "id"):
                    cid = f.get(key)
                    if cid and isinstance(cid, str):
                        finding_ids.add(cid)
                        if cid in TAXONOMY_ALIASES:
                            finding_ids.add(TAXONOMY_ALIASES[cid])
            elif isinstance(f, str):
                finding_ids.add(f)
                if f in TAXONOMY_ALIASES:
                    finding_ids.add(TAXONOMY_ALIASES[f])

        orientation_fail_triggers = {
            "LOW_INFORMATION_SCENT",
            "GENERIC_H1",
            "INTENT_SCENT_DILUTION",
            "HEADING_HIERARCHY_VACUUM",
        }
        handoff_fail_triggers = {
            "INTENT_TO_LANDING_MISMATCH",
            "CTA_REACHABILITY_FRICTION",
            "VIEWPORT_ANSWER_ABSENCE",
            "AGENT_INTERACTION_BARRIER",
            "AI_REFERRAL_DISCONTINUITY",
            "COMMERCIAL_HANDOFF_DISCONTINUITY",
            "ABOVE_FOLD_ACTION_DELAY",
        }

        if finding_ids.intersection(orientation_fail_triggers):
            nodes["on_site_orientation"] = "confirmed_fail"
        else:
            nodes["on_site_orientation"] = "confirmed_pass"

        if finding_ids.intersection(handoff_fail_triggers):
            nodes["engagement_handoff"] = "confirmed_fail"
        else:
            nodes["engagement_handoff"] = "confirmed_pass"
    else:
        nodes["on_site_orientation"] = "unknown"
        nodes["engagement_handoff"] = "unknown"

    return nodes


def main():
    import argparse
    import json
    import os
    import sys

    parser = argparse.ArgumentParser(
        description="Deterministic Causal DAG & Epistemic Falsification Engine CLI."
    )
    parser.add_argument("--telemetry", help="Path to telemetry JSON file")
    parser.add_argument("--findings", help="Path to findings JSON file (applies causal suppression)")
    parser.add_argument("--inventory", help="Path to site inventory JSON file")
    parser.add_argument("--output", "-o", help="Path to write output JSON (optional, defaults to stdout)")
    args = parser.parse_args()

    inv = {}
    specialist_results = {}
    findings_list = []

    if args.telemetry:
        if not os.path.exists(args.telemetry):
            sys.stderr.write(f"Error: Telemetry file {args.telemetry} not found\n")
            sys.exit(1)
        with open(args.telemetry, "r", encoding="utf-8") as f:
            t_data = json.load(f)
        inv = t_data.get("inventory", {})
        specialist_results = t_data.get("sensor_telemetry", {})
        for res in specialist_results.values():
            if isinstance(res, dict):
                findings_list.extend(res.get("findings", []))

    if args.inventory and os.path.exists(args.inventory):
        with open(args.inventory, "r", encoding="utf-8") as f:
            inv = json.load(f)

    if args.findings:
        if not os.path.exists(args.findings):
            sys.stderr.write(f"Error: Findings file {args.findings} not found\n")
            sys.exit(1)
        with open(args.findings, "r", encoding="utf-8") as f:
            f_data = json.load(f)
        findings_list = f_data.get("findings", f_data) if isinstance(f_data, dict) else f_data

    if not args.telemetry and not args.findings and not args.inventory:
        parser.print_help()
        return

    epistemic_state = evaluate_epistemic_state(inv, specialist_results)
    causal_nodes = evaluate_causal_nodes(inv, specialist_results)
    surviving_findings, suppressed, dag_metadata = apply_causal_suppression(findings_list)

    result = {
        "epistemic_state": epistemic_state,
        "causal_nodes": causal_nodes,
        "total_findings_evaluated": len(findings_list),
        "surviving_findings_count": len(surviving_findings),
        "suppressed_findings_count": len(suppressed),
        "suppressed_findings": suppressed,
        "surviving_findings": surviving_findings,
    }

    formatted = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
            f.write("\n")
        print(f"Causal analysis written to {args.output}")
    else:
        print(formatted)


if __name__ == "__main__":
    main()
