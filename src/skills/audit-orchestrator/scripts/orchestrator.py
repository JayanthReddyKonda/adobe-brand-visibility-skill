#!/usr/bin/env python3
"""
orchestrator.py - Master Orchestrator for Brand AI-Readiness & Visibility Audit.
Executes single-pass site acquisition, coordinates 6 specialist diagnostic sensors,
applies the full 6-layer Causal DAG and Keystone Defect deduplication, and emits a
strictly validated Draft-07 JSON report.
"""

import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Canonical Retrieval Bot Set (RFC 9309 search retrieval bots only — NOT training)
# Blocking these is a critical/high defect. Blocking training bots (GPTBot,
# ClaudeBot) is a governance decision — NOT an AI search defect.
# ---------------------------------------------------------------------------
RETRIEVAL_BOTS: Set[str] = {"OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "anthropic-ai"}

# ---------------------------------------------------------------------------
# Full 6-Layer Causal DAG — Keystone suppression tables
# Source: audit-orchestrator-knowledge-base.md Section 12
# Layer 0 defects preempt everything below. Layer 1 defects preempt Layers 2-4.
# ---------------------------------------------------------------------------
_LAYER0_CAUSE_IDS: Set[str] = {
    "AI_RETRIEVAL_BLOCKED",
    "NOINDEX_EXCLUSION",
    "ROBOTS_5XX_FAIL_CLOSED",
    "ROBOTS_TXT_OVERSIZED",
}
_LAYER1_CAUSE_IDS: Set[str] = {
    "RENDERED_CONTENT_GAP",
    "NOSNIPPET_ON_CORE_CONTENT",
    "WAF_BOT_CHALLENGE",
    "CANONICAL_FRAGMENTATION",
}
# Findings at Layers 2-5 that are symptoms of Layer 0 (access block)
_SUPPRESSED_BY_LAYER0: Set[str] = {
    # Layer 2 — Entity Resolution
    "MATERIAL_ENTITY_AMBIGUITY",
    "BROKEN_AUTHORITY_ANCHOR",
    "CIRCULAR_SAMEAS_SELF_REFERENCE",
    "WEAK_IDENTITY_SIGNALS",
    # Layer 3 — Fact Ledger
    "FIRST_PARTY_FACT_CONFLICT",
    "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
    "INCOMPLETE_OFFER_ATTRIBUTES",
    "STALE_AUTHORITATIVE_FACT",
    # Layer 4 — Citability
    "MISSING_IN_DEPTH_MECHANISMS",
    "STANDALONE_FAQ_DEFICIT",
    "LOW_FACT_TO_TOKEN_RATIO",
    "EXCESSIVE_KEYWORD_DENSITY",
    "CONTEXT_PLACEMENT_DEGRADATION",
    "LOW_INFORMATION_SCENT",
    # Layer 5 — Engine selection (full suppression only when entire domain is blocked)
    "AI_CITATION_GAP",
    "AI_FACT_CONFLICT",
    "AI_REFERRAL_DISCONTINUITY",
    "INTENT_TO_LANDING_MISMATCH",
}
# Findings at Layers 3-4 that are symptoms of Layer 1 (rendering gap)
_SUPPRESSED_BY_LAYER1: Set[str] = {
    # Layer 3 — cannot read facts from an unrendered shell
    "FIRST_PARTY_FACT_CONFLICT",
    "INCOMPLETE_OFFER_ATTRIBUTES",
    "ATTRIBUTE_INCOMPLETENESS",
    # Layer 4 — cannot evaluate citation quality of an empty page
    "LOW_FACT_TO_TOKEN_RATIO",
    "MISSING_IN_DEPTH_MECHANISMS",
    "CONTEXT_PLACEMENT_DEGRADATION",
    "LOW_CITABILITY_SCORE",
    "LACK_OF_SPECIFIC_EVIDENCE",
}

# ---------------------------------------------------------------------------
# Archetype-Specific Severity Reweighting
# Scripts detect the archetype; AI contextualizes defect severity by business model.
# Source: audit-orchestrator-knowledge-base.md Section 7 & 8
# ---------------------------------------------------------------------------
ARCHETYPE_SEVERITY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "ecommerce": {
        # Product schema without price/availability is critical for purchase journeys
        "ATTRIBUTE_INCOMPLETENESS": "critical",
        "INCOMPLETE_OFFER_ATTRIBUTES": "critical",
        "COMMERCIAL_PRODUCT_DATA_CONTRADICTION": "critical",
        # AI must recommend specific products; entity ambiguity is high not medium
        "MATERIAL_ENTITY_AMBIGUITY": "high",
        # Fact conflicts on pricing pages mislead buyers
        "FIRST_PARTY_FACT_CONFLICT": "critical",
    },
    "saas": {
        # SaaS buyers need feature comparisons; thin content blocks category citations
        "LOW_FACT_TO_TOKEN_RATIO": "high",
        "MISSING_IN_DEPTH_MECHANISMS": "high",
        # Pricing clarity is critical for AI buying agents
        "FIRST_PARTY_FACT_CONFLICT": "critical",
        "CONTEXT_PLACEMENT_DEGRADATION": "high",
    },
    "publisher": {
        # E-E-A-T authorship is critical for publisher citation in AI Overviews
        "MATERIAL_ENTITY_AMBIGUITY": "high",
        # FAQ structure deficits are more impactful for reference/how-to content
        "STANDALONE_FAQ_DEFICIT": "high",
        # Fact currency matters more for news/publisher sites
        "STALE_AUTHORITATIVE_FACT": "high",
        "CONTENT_RECENCY_DEFICIT": "medium",
    },
    "local_business": {
        # Local AI assistants (Maps, voice search) cannot surface hours/address without LocalBusiness schema
        "MATERIAL_ENTITY_AMBIGUITY": "critical",
        "MISSING_MATERIAL_FACT": "critical",
        # Broken authority anchors on Google Business Profile = critical for local discovery
        "BROKEN_AUTHORITY_ANCHOR": "high",
    },
    "corporate": {},  # Use default sensor severities
}

# Ensure local script directory and peer skill script directories are in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SKILLS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

for skill_name in [
    "web-scraper",
    "discoverability-audit",
    "entity-content-audit",
    "fact-consistency-audit",
    "corroboration-authority-audit",
    "geo-content-audit",
    "engagement-context-audit",
]:
    p = os.path.join(SKILLS_DIR, skill_name, "scripts")
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from acquire_inventory import build_inventory
except ImportError:
    build_inventory = None  # type: ignore

try:
    from validate_report import validate_type
except ImportError:
    validate_type = None  # type: ignore

try:
    from causal_gate import (
        DEFAULT_LIMITATIONS,
        LAYER0_CAUSE_IDS,
        LAYER1_CAUSE_IDS,
        ROOT_CAUSE_PRECEDENCE,
        SUPPRESSED_BY_LAYER0,
        SUPPRESSED_BY_LAYER1,
        apply_causal_suppression,
        build_evidence_index,
        compute_archetype_confidence,
        compute_severity_score,
        evaluate_causal_nodes,
        evaluate_epistemic_state,
        severity_from_score,
    )
except ImportError:
    apply_causal_suppression = None  # type: ignore
    build_evidence_index = None  # type: ignore
    evaluate_epistemic_state = None  # type: ignore
    evaluate_causal_nodes = None  # type: ignore
    compute_severity_score = None  # type: ignore
    compute_archetype_confidence = None  # type: ignore
    severity_from_score = None  # type: ignore
    LAYER0_CAUSE_IDS = _LAYER0_CAUSE_IDS
    LAYER1_CAUSE_IDS = _LAYER1_CAUSE_IDS
    SUPPRESSED_BY_LAYER0 = _SUPPRESSED_BY_LAYER0
    SUPPRESSED_BY_LAYER1 = _SUPPRESSED_BY_LAYER1
    DEFAULT_LIMITATIONS = [
        "No JavaScript browser rendering was performed.",
        "Robots eligibility was simulated from the captured robots.txt; bot-specific server responses were not tested.",
        "No external analytics were supplied, so engagement findings are content and navigation proxies rather than observed bounce rates.",
        "No claim is made about actual citation by any specific AI assistant.",
    ]
    ROOT_CAUSE_PRECEDENCE = [
        "SITE_UNAVAILABLE_OR_BLOCKED",
        "AI_RETRIEVAL_BLOCKED",
        "INDEXING_DISABLED",
        "CLIENT_RENDERING_DEPENDENCY",
        "ENTITY_AMBIGUITY",
        "FACT_CONTRADICTION",
        "LOW_CITABILITY",
        "ENGAGEMENT_HANDOFF_FRICTION",
    ]


def parse_target_domain(site: str) -> tuple:
    """Normalize site string into base URL and domain."""
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    parsed = urlparse(site)
    domain = parsed.netloc or parsed.path.split("/")[0]
    base = f"{parsed.scheme}://{domain}"
    return base, domain


def load_schema() -> Dict[str, Any]:
    """Load canonical Draft-07 report schema. Fails closed if missing or corrupt."""
    schema_path = os.path.join(os.path.dirname(SCRIPT_DIR), "references", "report-schema.json")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Canonical report schema missing at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_text_string(val: Any) -> str:
    """Normalize string for clean JSON report output, eliminating literal newlines, raw tables, and redundant whitespace."""
    if val is None:
        return ""
    if isinstance(val, (tuple, list)):
        return " ; ".join(clean_text_string(x) for x in val if x)
    text = str(val)
    # Strip markdown table delimiter lines e.g. |---|---| or |:---:|:---:|
    text = re.sub(r"\|(?:\s*:?-+:?\s*\|)+", " ", text)
    # Strip leading and trailing table pipes e.g. | col1 | col2 | -> col1 ; col2
    text = re.sub(r"(?m)^\s*\|\s*", "", text)
    text = re.sub(r"(?m)\s*\|\s*$", "", text)
    text = re.sub(r"\s*\|\s*", " ; ", text)
    # If text has newlines between sentences (ends with punctuation), replace with space
    text = re.sub(r"([.!?])\s*[\r\n]+\s*", r"\1 ", text)
    # If text has code/config lines (like robots.txt or markdown lists), join with ' ; '
    text = re.sub(r"\s*[\r\n]+\s*", " ; ", text)
    # Clean up duplicated semicolons and spaces
    text = re.sub(r"(?:\s*;\s*)+", " ; ", text)
    text = re.sub(r"[ \t]+", " ", text).strip(" ;")
    return text.strip()


def run_specialist_sensor(sensor_func, base: str, domain: str, inv: Dict[str, Any], extra_arg=None) -> Dict[str, Any]:
    """Safely execute a specialist sensor with defensive error handling."""
    try:
        if extra_arg is not None:
            return sensor_func(base, domain, inv=inv, **extra_arg)
        return sensor_func(base, domain, inv=inv)
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Sensor exception: {type(e).__name__}: {e}",
            "findings": [],
            "recommendations": [],
        }


def detect_business_archetype(inv: Dict[str, Any]) -> str:
    """Classifies website into primary business archetype from crawl inventory."""
    pages = inv.get("pages", []) if inv else []
    if not pages:
        return "corporate"

    ecomm_score = 0
    saas_score = 0
    publisher_score = 0
    local_score = 0

    for p in pages:
        ptype = (p.get("page_type") or "").lower()
        url = (p.get("url") or "").lower()
        html = (p.get("html") or "").lower()

        if ptype in ("product_detail", "product", "product_listing", "category") or any(
            k in url for k in ("/product", "/shop", "/item", "/store", "/collection", "/catalog")
        ):
            ecomm_score += 2
        if "schema.org/product" in html or "schema.org/offer" in html or '"@type": "product"' in html:
            ecomm_score += 3

        if ptype in ("pricing", "subscription_flow", "documentation") or any(
            k in url for k in ("/pricing", "/plans", "/docs", "/api", "/billing", "/features")
        ):
            saas_score += 2
        if "softwareapplication" in html or '"@type": "softwareapplication"' in html:
            saas_score += 3

        if ptype == "article" or any(k in url for k in ("/blog", "/news", "/article", "/post", "/journal")):
            publisher_score += 2
        if "newsarticle" in html or "blogposting" in html or '"@type": "article"' in html:
            publisher_score += 3

        if ptype == "location" or any(k in url for k in ("/location", "/store-locator", "/contact", "/branches")):
            local_score += 1
        if "localbusiness" in html or "postaladdress" in html:
            local_score += 3

    candidates = [
        (ecomm_score, "ecommerce"),
        (saas_score, "saas"),
        (publisher_score, "publisher"),
        (local_score, "local_business"),
    ]
    candidates.sort(key=lambda x: x[0], reverse=True)
    if candidates[0][0] >= 2:
        return candidates[0][1]
    return "corporate"


def synthesize_audit_report(
    site: str,
    inv: Dict[str, Any],
    specialist_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply Causal DAG, Keystone Defect deduplication, and Draft-07 synthesis."""
    base, domain = parse_target_domain(site)
    pages = inv.get("pages", []) if inv else []
    _domain_clean = domain.split(":")[0]
    _brand_guess = _domain_clean.split(".")[0].capitalize()

    for p in pages:
        p_html = p.get("html") or ""
        m_og = re.search(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']', p_html, re.I)
        if m_og and m_og.group(1).strip():
            _brand_guess = m_og.group(1).strip()
            break
        m_title = re.search(r'<title[^>]*>([^<]+)</title>', p_html, re.I)
        if m_title and m_title.group(1).strip():
            t_raw = m_title.group(1).strip()
            t_parts = re.split(r'[\s|:–—\-]+', t_raw)
            if t_parts and len(t_parts[0]) > 1:
                _brand_guess = t_parts[0].strip()
                break

    sample_routes: List[str] = []
    sample_product_route = None
    sample_pricing_route = None
    for p in pages:
        p_url = p.get("url") or ""
        parsed_p = urlparse(p_url)
        path = parsed_p.path or "/"
        if path not in ("/", "") and path not in sample_routes:
            sample_routes.append(path)
        if not sample_product_route and any(k in path.lower() for k in ("/product", "/item", "/shop", "/catalog")):
            sample_product_route = path
        if not sample_pricing_route and any(k in path.lower() for k in ("/pricing", "/plans", "/billing")):
            sample_pricing_route = path

    has_llms_txt = any("llms.txt" in (p.get("url") or "").lower() for p in pages) or bool(inv.get("llms_txt") if inv else False)

    all_raw_findings: List[Dict[str, Any]] = []
    all_raw_recommendations: List[Dict[str, Any]] = []

    statuses = []
    for _skill_name, result in specialist_results.items():
        statuses.append(result.get("status", "ok"))
        all_raw_findings.extend(result.get("findings", []))
        all_raw_recommendations.extend(result.get("recommendations", []))

    if inv.get("status") == "failed" or (not pages and not inv.get("infrastructure", {}).get("homepage_reachable", True)):
        audit_status = "failed"
    elif all(s == "ok" for s in statuses):
        audit_status = "complete"
    elif any(s in ("ok", "inconclusive") for s in statuses):
        audit_status = "partial"
    else:
        audit_status = "failed"

    # 1. Full 6-Layer Causal DAG Precedence Analysis & Keystone Defect Identification
    # (Source: audit-orchestrator-knowledge-base.md Section 12)
    def _is_sitewide_l0(f: Dict[str, Any]) -> bool:
        c_id = f.get("cause_id") or f.get("id", "")
        if c_id not in _LAYER0_CAUSE_IDS:
            return False
        if c_id in ("ROBOTS_5XX_FAIL_CLOSED", "ROBOTS_TXT_OVERSIZED", "DNS_UNREACHABLE", "HTTP_RETRIEVAL_ZERO"):
            return True
        ev = str(f.get("evidence", "")).lower()
        root = str(f.get("root_cause", "")).lower()
        if c_id == "NOINDEX_EXCLUSION" and ("sitewide" in ev or "homepage" in ev or f.get("scope") in ("/", base, domain)):
            return True
        if c_id == "AI_RETRIEVAL_BLOCKED":
            if "disallows all" in root or "disallow: / " in ev or "disallow: /\n" in ev:
                return True
            if "disallow: /" in ev and not any(sub in ev for sub in ("/blog", "/admin", "/cart", "/checkout", "/api", "/content")):
                return True
        return False

    has_sitewide_layer0_block = any(_is_sitewide_l0(f) for f in all_raw_findings)
    layer0_blocked_pages = {
        str(f.get("url") or f.get("scope") or (f.get("evidence", {}).get("scope") if isinstance(f.get("evidence"), dict) else "")).lower()
        for f in all_raw_findings
        if (f.get("cause_id") or f.get("id", "")) in _LAYER0_CAUSE_IDS
    }
    layer0_blocked_pages = {p for p in layer0_blocked_pages if p}
    rendering_gap_findings = [
        f for f in all_raw_findings
        if (f.get("cause_id") or f.get("id", "")) in _LAYER1_CAUSE_IDS
    ]
    has_layer1_rendering_gap = bool(rendering_gap_findings)
    rendering_gap_pages = {
        str(f.get("url") or f.get("scope") or (f.get("evidence", {}).get("scope") if isinstance(f.get("evidence"), dict) else "")).lower()
        for f in rendering_gap_findings
    }
    rendering_gap_pages = {p for p in rendering_gap_pages if p}
    # Site-wide only if all pages have low word count or single homepage crawl is a shell
    home_page_obj = next((p for p in pages if (p.get("url") or "").rstrip("/") == base.rstrip("/")), pages[0] if pages else {})
    home_wc = home_page_obj.get("word_count", 0)
    is_site_wide_rendering_gap = (
        has_layer1_rendering_gap and (
            (home_wc < 30 and home_wc > 0)
            or (pages and all(p.get("word_count", 0) < 60 for p in pages))
        )
    )

    # 2. Scope-Aware Deduplication of Findings
    deduped_findings: List[Dict[str, Any]] = []
    seen_dedup_keys: Set[str] = set()
    finding_counter = 1

    # Order by severity: critical -> high -> medium -> low
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    all_raw_findings.sort(key=lambda f: severity_rank.get(f.get("severity", "low"), 1), reverse=True)

    for f in all_raw_findings:
        cid = f.get("cause_id") or f.get("id") or f.get("title", "")
        f_scope = str(f.get("scope") or f.get("entity") or f.get("attribute") or f.get("url") or "").lower()
        if isinstance(f.get("evidence"), dict):
            f_scope = f_scope or str(f["evidence"].get("scope", "")).lower()

        # Full 6-Layer Causal DAG Keystone Suppression (P0-11):
        # Layer 0 access block preempts downstream symptoms if site-wide or on the specific blocked page
        if has_sitewide_layer0_block and cid in _SUPPRESSED_BY_LAYER0:
            continue
        if f_scope and any(blk in f_scope or f_scope in blk for blk in layer0_blocked_pages) and cid in _SUPPRESSED_BY_LAYER0:
            continue
        # Layer 1 rendering gap only suppresses downstream if site-wide or on the specific unrendered page
        if is_site_wide_rendering_gap and cid in _SUPPRESSED_BY_LAYER1:
            continue
        if f_scope and any(gap in f_scope or f_scope in gap for gap in rendering_gap_pages) and cid in _SUPPRESSED_BY_LAYER1:
            continue

        # P0-10: Deduplicate identical findings across routes by root cause and title (clean, non-mutating)
        dedup_key = f"{cid}::{f.get('title', '')}"
        if dedup_key in seen_dedup_keys:
            continue
        seen_dedup_keys.add(dedup_key)

        # P0-15: Never fabricate synthetic evidence text. Discard findings without observable proof.
        raw_ev = f.get("evidence")
        if not raw_ev:
            continue

        finding_id = f"F-{finding_counter:03d}"
        finding_counter += 1

        raw_sev = f.get("severity", "medium")
        sev = str(raw_sev).lower() if raw_sev is not None else "medium"
        if sev not in ("critical", "high", "medium", "low"):
            sev = "medium"

        raw_ftitle = f.get("title", "Detected Brand Visibility Defect")
        f_title = clean_text_string(raw_ftitle)

        # P0-14: Require mechanism root cause; do not default to title
        raw_froot = f.get("root_cause") or f.get("cause_id") or "Mechanism unconfirmed / unknown"
        f_root = clean_text_string(raw_froot)

        # P0-13: Missing or invalid confidence defaults to 'low', never 'high'
        raw_conf = str(f.get("confidence") or "").lower()
        conf = raw_conf if raw_conf in ("high", "medium", "low") else "low"
        if not f.get("root_cause") and not f.get("cause_id"):
            conf = "low"

        action = f.get("suggested_action") or {}
        raw_act_sum = action.get("summary") or f.get("title") or f"Remediate {f_title.lower()} on target domain {domain}."
        action_summary = clean_text_string(raw_act_sum)

        raw_act_prio = action.get("priority") or sev
        action_priority = str(raw_act_prio).lower() if raw_act_prio is not None else sev
        if action_priority not in ("critical", "high", "medium", "low"):
            action_priority = sev

        # Structure evidence strictly according to the Top-Tier contract
        target_src_type = "first_party"
        if "ROBOTS" in cid or "BOT" in cid:
            target_src_type = "robots"
        elif "SITEMAP" in cid:
            target_src_type = "sitemap"
        elif any(k in cid for k in ("SCHEMA", "JSONLD", "ENTITY", "ATTRIBUTE")):
            target_src_type = "structured_data"
        elif any(k in cid for k in ("RENDER", "CSR", "WORD", "TEXT")):
            target_src_type = "visible_content"
        elif any(k in cid for k in ("CORROBORATION", "AUTHORITY", "WIKIDATA", "LINKEDIN")):
            target_src_type = "third_party"
        elif any(k in cid for k in ("HTTP", "STATUS", "REDIRECT")):
            target_src_type = "http"

        sample_url = f.get("url") or (f.get("evidence_refs", [None])[0] if f.get("evidence_refs") else None) or f"{base}/"

        if isinstance(raw_ev, dict) and "sources" in raw_ev and isinstance(raw_ev["sources"], list):
            evidence_val: Dict[str, Any] = {
                "summary": clean_text_string(raw_ev.get("summary") or f_title),
                "sources": [
                    {
                        "url": str(s.get("url") or sample_url),
                        "type": str(s.get("type") or target_src_type),
                        "observation": clean_text_string(s.get("observation") or str(s)),
                    }
                    for s in raw_ev["sources"] if isinstance(s, dict)
                ],
            }
            if not evidence_val["sources"]:
                evidence_val["sources"].append({
                    "url": sample_url,
                    "type": target_src_type,
                    "observation": clean_text_string(raw_ev.get("summary") or f_title),
                })
        elif isinstance(raw_ev, dict):
            ev_summary = clean_text_string(raw_ev.get("summary") or raw_ev.get("observation") or f_title)
            ev_obs = clean_text_string(raw_ev.get("observation") or raw_ev.get("details") or str(raw_ev))
            evidence_val = {
                "summary": ev_summary,
                "sources": [
                    {
                        "url": str(raw_ev.get("url") or sample_url),
                        "type": str(raw_ev.get("type") or target_src_type),
                        "observation": ev_obs,
                    }
                ],
            }
        elif isinstance(raw_ev, str):
            ev_summary = clean_text_string(raw_ev)
            evidence_val = {
                "summary": ev_summary,
                "sources": [
                    {
                        "url": sample_url,
                        "type": target_src_type,
                        "observation": ev_summary,
                    }
                ],
            }
        else:
            ev_str = clean_text_string(str(raw_ev))
            evidence_val = {
                "summary": ev_str,
                "sources": [
                    {
                        "url": sample_url,
                        "type": target_src_type,
                        "observation": ev_str,
                    }
                ],
            }

        suggested_action: Dict[str, Any] = {
            "summary": action_summary,
            "technical_fix": clean_text_string(action.get("technical_fix")) or None,
            "creative_fix": clean_text_string(action.get("creative_fix")) or None,
            "priority": action_priority,
            "verification": clean_text_string(action.get("verification")) or None,
        }

        actual_band = f.get("actual_band") or {"critical": "S4", "high": "S3", "medium": "S2", "low": "S1"}.get(sev, "S2")
        diff = f.get("difficulty")
        prio_idx = None
        if isinstance(diff, int) and 1 <= diff <= 5:
            prio_idx = 5 * int(actual_band[1]) + (6 - diff)

        raw_impact = f.get("impact") or f.get("impact_estimate")
        if not raw_impact:
            cat = str(f.get("category", "discoverability"))
            if cat in ("discoverability", "crawlability"):
                raw_impact = "Impairs AI crawler indexation, causing the domain or catalog to be omitted from AI search retrieval."
            elif cat == "fact_consistency":
                raw_impact = "Conflicting first-party facts reduce model consensus confidence, leading to hallucinations or citation exclusion."
            elif cat == "entity_content":
                raw_impact = "Ambiguous entity and product attributes prevent generative engines from answering user purchase queries directly."
            elif cat == "corroboration":
                raw_impact = "Lack of third-party authority links weakens brand identity verification across external knowledge graphs."
            elif cat == "geo_content":
                raw_impact = "Low statistical density and absent direct-answer formatting depress citation frequency in generative response engines."
            else:
                raw_impact = "Degrades post-citation visitor orientation and decreases intent-handoff retention."

        clean_finding: Dict[str, Any] = {
            "id": finding_id,
            "cause_id": cid,
            "title": f_title,
            "severity": sev,
            "category": str(f.get("category", "discoverability")),
            "root_cause": f_root,
            "confidence": conf,
            "evidence": evidence_val,
            "impact": clean_text_string(raw_impact),
            "suggested_action": suggested_action,
        }

        if f.get("scope"):
            clean_finding["scope"] = f["scope"]
        if prio_idx is not None:
            clean_finding["priority_index"] = prio_idx
        if f.get("depends_on"):
            clean_finding["depends_on"] = f["depends_on"]

        deduped_findings.append(clean_finding)

    # 3. Archetype Detection, Severity Reweighting & Proactive Opportunities Synthesis
    archetype = detect_business_archetype(inv)
    # contextualizes severity by business model — missing Product schema is medium for a
    # corporate blog but critical for an e-commerce product page.
    archetype_overrides = ARCHETYPE_SEVERITY_OVERRIDES.get(archetype, {})
    if archetype_overrides:
        for finding in deduped_findings:
            f_cid = finding.get("cause_id") or finding.get("root_cause", "")
            # Match on cause_id OR the finding id string for broad coverage
            for override_cid, override_sev in archetype_overrides.items():
                if override_cid in f_cid or override_cid in (finding.get("id") or ""):
                    original_sev = finding.get("severity", "medium")
                    if severity_rank.get(override_sev, 1) > severity_rank.get(original_sev, 1):
                        finding["severity"] = override_sev
                        if finding.get("suggested_action"):
                            finding["suggested_action"]["priority"] = override_sev

    # Re-sync actual_band and priority_index after archetype reweighting
    band_map = {"critical": "S4", "high": "S3", "medium": "S2", "low": "S1"}
    for finding in deduped_findings:
        finding["actual_band"] = band_map.get(finding.get("severity", "medium"), "S2")
        diff = finding.get("difficulty")
        if isinstance(diff, int) and 1 <= diff <= 5:
            finding["priority_index"] = 5 * int(finding["actual_band"][1]) + (6 - diff)

    # Queue and Dependency-aware Topological Task Sort
    queues = {"confirmed": 0, "advisory": 1, "investigation": 2}

    def task_sort_key(item: Dict[str, Any]) -> tuple:
        band = item.get("actual_band", "S2")
        sev_num = int(band[1]) if band.startswith("S") and len(band) > 1 else 1
        d = item.get("difficulty")
        q = queues.get(item.get("queue", "confirmed"), 0)
        return (q, -sev_num, d if d is not None else 0, item.get("id", ""))

    has_deps = any(f.get("depends_on") for f in deduped_findings)
    if has_deps:
        pending = {f["id"]: f for f in deduped_findings}
        done: Set[str] = set()
        sorted_output: List[Dict[str, Any]] = []
        while pending:
            available = [
                f for f in pending.values()
                if set(f.get("depends_on", [])) <= done or not any(d in pending for d in f.get("depends_on", []))
            ]
            if not available:
                break
            first = min(available, key=task_sort_key)
            sorted_output.append(first)
            done.add(first["id"])
            del pending[first["id"]]
        for rem in sorted(pending.values(), key=task_sort_key):
            sorted_output.append(rem)
        deduped_findings = sorted_output
    else:
        deduped_findings.sort(key=task_sort_key)

    # Re-compute counts after reweighting
    crit_count = sum(1 for f in deduped_findings if f["severity"] == "critical")
    high_count = sum(1 for f in deduped_findings if f["severity"] == "high")
    med_count = sum(1 for f in deduped_findings if f["severity"] == "medium")
    low_count = sum(1 for f in deduped_findings if f["severity"] == "low")

    # -------------------------------------------------------------------------
    # Proactive Actions (Strategic forward-looking enhancements ONLY)
    # Genuinely proactive initiatives that do NOT duplicate explicit defects.
    # -------------------------------------------------------------------------
    finding_cids = {f.get("cause_id", "") for f in deduped_findings}
    target_route = sample_product_route or (f"https://{domain}/products" if domain else "catalog routes")
    pricing_source = sample_pricing_route or (f"https://{domain}/pricing" if domain else "pricing routes")
    route_refs = ", ".join(sample_routes[:3]) if sample_routes else (f"https://{domain}/" if domain else "core routes")

    proactive_actions: List[Dict[str, Any]] = []
    proactive_counter = 1

    # 1. Authoritative LLM Index Manifest (/llms.txt)
    if has_llms_txt:
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Audit & Expand Existing /llms.txt Manifest for {_brand_guess}",
            "category": "discoverability",
            "summary": f"Authoritative /llms.txt detected on {domain}. Audit section anchors and BLUF summaries to ensure comprehensive alignment with core guides.",
            "priority": "low",
            "technical_fix": f"Validate https://{domain}/llms.txt against llmstxt.org specification, linking directly to: {route_refs}.",
            "creative_fix": f"Author first-100-word executive overviews for every core {_brand_guess} product and documentation guide.",
            "verification": f"Request GET https://{domain}/llms.txt and verify HTTP 200 with non-empty plain-text markdown.",
        })
        proactive_counter += 1
    else:
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Deploy Machine-Readable /llms.txt Manifest for {_brand_guess}",
            "category": "discoverability",
            "summary": f"Deploy an authoritative /llms.txt manifest at https://{domain}/llms.txt with BLUF summaries and clean markdown links for generative search assistants.",
            "priority": "low",
            "technical_fix": f"Serve /llms.txt at https://{domain}/llms.txt over HTTPS with Content-Type: text/plain and links to primary routes: {route_refs}.",
            "creative_fix": f"Author first-100-word executive overviews for every core {_brand_guess} service guide.",
            "verification": f"Request GET https://{domain}/llms.txt and verify HTTP 200 with non-empty plain-text markdown.",
        })
        proactive_counter += 1

    # 2. Dynamic Edge Markdown Negotiation (Zero-token retrieval) if no rendering gap
    if "RENDERED_CONTENT_GAP" not in finding_cids:
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": "Enable Edge Markdown Content Negotiation for AI Indexers",
            "category": "discoverability",
            "summary": "Configure web server or CDN to serve pre-rendered clean markdown when requests include Accept: text/markdown, cutting AI token ingestion cost by 80%.",
            "priority": "low",
            "technical_fix": "Configure CDN edge worker to inspect Accept header and serve pre-generated markdown for AI crawlers.",
            "creative_fix": "Author clean markdown equivalents of core landing pages stripped of layout markup and navigation chrome.",
            "verification": f"Request curl -H 'Accept: text/markdown' https://{domain}/ and verify HTTP 200 with text/markdown Content-Type.",
        })
        proactive_counter += 1

    # 3. Archetype Strategic Enhancements (Only if NO corresponding defect exists)
    if archetype == "ecommerce" and "ATTRIBUTE_INCOMPLETENESS" not in finding_cids:
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Implement Structured Specification Comparison Tables for {_brand_guess}",
            "category": "entity",
            "summary": "Embed semantic HTML tables detailing product dimensions, materials, and origin to maximize conversational recommendations in ChatGPT Search and Perplexity.",
            "priority": "low",
            "technical_fix": f"Embed responsive HTML <table> markup on {target_route} with clean headers and numeric specifications.",
            "creative_fix": "Structure product feature specifications into quantitative rows (weight, extraction ratio, temperature).",
            "verification": f"Verify presence of semantic table elements in HTML of {target_route}.",
        })
        proactive_counter += 1
    elif archetype == "saas" and "FIRST_PARTY_FACT_CONFLICT" not in finding_cids:
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Deploy Autonomous AI Purchasing Agent Pricing Manifest (/pricing.md) for {_brand_guess}",
            "category": "fact_consistency",
            "summary": "Expose an un-gated, machine-readable /pricing.md endpoint detailing plan tiers, token limits, seat costs, and API overage rates for autonomous AI purchasing agents.",
            "priority": "low",
            "technical_fix": f"Serve /pricing.md at https://{domain}/pricing.md with structured plan comparison tables extracted from {pricing_source}.",
            "creative_fix": f"Standardize plan names across {pricing_source} with transparent feature contrast rows.",
            "verification": f"Request GET https://{domain}/pricing.md and verify HTTP 200 with text/markdown Content-Type.",
        })
        proactive_counter += 1
    elif archetype == "publisher" and "MATERIAL_ENTITY_AMBIGUITY" not in finding_cids:
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Structure E-E-A-T Author Credentials & Fact Attributions for {_brand_guess}",
            "category": "entity",
            "summary": f"Embed Schema.org Person markup for {_brand_guess} editorial staff linking to verified LinkedIn/Wikidata profiles and structure 40–60 word BLUF answer blocks beneath question headings.",
            "priority": "low",
            "technical_fix": f"Embed Schema.org NewsArticle with Person authorship and sameAs links to external credential profiles on {base}/.",
            "creative_fix": "Replace passive voice with attributed expert quotes and verifiable benchmark statistics (+40.9% Princeton GEO lift).",
            "verification": f"Inspect article markup on https://{domain}/ with Google Rich Results Test to confirm valid Person credentials.",
        })
        proactive_counter += 1
    elif "MATERIAL_ENTITY_AMBIGUITY" not in finding_cids and "WEAK_IDENTITY_SIGNALS" not in finding_cids:
        corrob_res_p = specialist_results.get("corroboration-authority-audit", {})
        corrob_cov_p = corrob_res_p.get("coverage", {})
        p_sa_count = corrob_cov_p.get("sameas_declared", corrob_cov_p.get("sameas_count", 0)) or 0
        if p_sa_count > 0:
            proactive_actions.append({
                "id": f"P-{proactive_counter:03d}",
                "title": f"Expand Knowledge Graph Authority Anchors for {_brand_guess}",
                "category": "corroboration",
                "summary": f"{_brand_guess} currently declares {p_sa_count} sameAs node(s). Expand third-party authority coverage with Wikidata and LinkedIn verification.",
                "priority": "low",
                "technical_fix": f"Add verified Wikidata entity URI and official LinkedIn organization profile to Schema.org Organization on https://{domain}/.",
                "creative_fix": f"Maintain identical legal name '{_brand_guess}' and contact details across all registered external profiles.",
                "verification": f"Inspect root HTML JSON-LD on https://{domain}/ with Google Rich Results Test or Schema.org Validator.",
            })
            proactive_counter += 1

    # 4. Princeton Citability Architecture (Only if citability defects are not already flagged)
    if not any(c in finding_cids for c in ("LOW_CITABILITY_SCORE", "LOW_FACT_TO_TOKEN_RATIO", "STANDALONE_FAQ_DEFICIT", "MISSING_IN_DEPTH_MECHANISMS")):
        proactive_actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Implement Princeton KDD 2024 Citability Architecture on {domain}",
            "category": "geo_content",
            "summary": f"Structure core sections on {domain} into 134-167 word standalone passages under conversational question headings to maximize RAG snippet absorption.",
            "priority": "low",
            "technical_fix": f"Structure {domain} content under H2/H3 question headers with 40-60 word BLUF answers and semantic bullet lists.",
            "creative_fix": f"Eliminate exophoric pronouns in section leads ('It', 'They', 'We'); state canonical entity name '{_brand_guess}' directly.",
            "verification": f"Audit {domain} section word counts and verify presence of causal conjunctions ('because', 'therefore', 'enables').",
        })
        proactive_counter += 1

    final_proactive = proactive_actions[:3]
    for idx, act in enumerate(final_proactive, start=1):
        act["id"] = f"P-{idx:03d}"

    # 4. Counts-by-Severity Summary (computed earlier after archetype reweighting)
    # (crit_count, high_count, med_count, low_count already set above)

    # 6. Assemble Final Draft-07 Compliant Report (Signal Only, Zero Bloat)
    report: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "site": site,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "audit_status": audit_status,
        "summary": {
            "total_findings": len(deduped_findings),
            "critical": crit_count,
            "high": high_count,
            "medium": med_count,
            "low": low_count,
        },
        "findings": deduped_findings,
        "proactive_actions": final_proactive,
    }

    return report


def collect_telemetry(
    site: str,
    inventory: Optional[str] = None,
    analytics: Optional[str] = None,
    candidate_backlinks: Optional[str] = None,
) -> tuple:
    """Acquire inventory and execute all 6 specialist sensors, returning (inv, specialist_results)."""
    base, domain = parse_target_domain(site)

    # 1. Acquire or load inventory
    inv: Optional[Dict[str, Any]] = None
    if inventory:
        if isinstance(inventory, dict):
            inv = inventory
        elif isinstance(inventory, (str, bytes, os.PathLike)) and os.path.exists(inventory):
            try:
                with open(inventory, "r", encoding="utf-8") as f:
                    inv = json.load(f)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to load inventory from {inventory}: {e}\n")
                inv = {"pages": [], "error": f"Failed to parse inventory: {e}", "status": "failed"}
        else:
            inv = {"pages": [], "error": f"Inventory path {inventory} not found", "status": "failed"}

    if inv is None:
        if build_inventory is not None:
            try:
                inv_res = build_inventory(site, max_pages=15, timeout_seconds=60)
                if isinstance(inv_res, tuple):
                    inv_candidate, stats = inv_res
                    if isinstance(inv_candidate, dict):
                        inv = inv_candidate
                        if "stats" not in inv and isinstance(stats, dict):
                            inv["stats"] = stats
                elif isinstance(inv_res, dict):
                    inv = inv_res
            except Exception as e:
                sys.stderr.write(f"Warning: Live inventory acquisition failed: {e}\n")
                inv = None

        if inv is None or not isinstance(inv, dict):
            inv = {
                "site": site,
                "domain": domain,
                "status": "failed",
                "error": {
                    "type": "acquisition_failure",
                    "message": f"Target {site} was unreachable or inventory acquisition failed.",
                    "url": site,
                },
                "pages": [],
                "robots": {},
                "sitemaps": [],
            }

    # 2. Execute all 6 specialist sensors
    specialist_results: Dict[str, Dict[str, Any]] = {}

    if inv.get("status") == "failed":
        # Epistemic invariant (P0-1): Never synthesize evidence when acquisition fails.
        for skill_id in [
            "discoverability-audit",
            "entity-content-audit",
            "fact-consistency-audit",
            "corroboration-authority-audit",
            "geo-content-audit",
            "engagement-context-audit",
        ]:
            specialist_results[skill_id] = {
                "status": "inconclusive",
                "findings": [],
                "recommendations": [],
                "error": inv.get("error"),
            }
        return inv, specialist_results

    try:
        from discoverability_check import audit as audit_disc
        specialist_results["discoverability-audit"] = run_specialist_sensor(audit_disc, base, domain, inv)
    except Exception:
        specialist_results["discoverability-audit"] = {"status": "inconclusive", "findings": [], "recommendations": []}

    try:
        from entity_content_check import audit as audit_entity
        specialist_results["entity-content-audit"] = run_specialist_sensor(audit_entity, base, domain, inv)
    except Exception:
        specialist_results["entity-content-audit"] = {"status": "inconclusive", "findings": [], "recommendations": []}

    try:
        from fact_consistency_check import audit as audit_fact
        specialist_results["fact-consistency-audit"] = run_specialist_sensor(audit_fact, base, domain, inv)
    except Exception:
        specialist_results["fact-consistency-audit"] = {"status": "inconclusive", "findings": [], "recommendations": []}

    try:
        from corroboration_check import audit as audit_corrob
        extra = {"candidate_backlinks": candidate_backlinks} if candidate_backlinks else None
        specialist_results["corroboration-authority-audit"] = run_specialist_sensor(audit_corrob, base, domain, inv, extra)
    except Exception:
        specialist_results["corroboration-authority-audit"] = {"status": "inconclusive", "findings": [], "recommendations": []}

    try:
        from geo_content_check import audit as audit_geo
        specialist_results["geo-content-audit"] = run_specialist_sensor(audit_geo, base, domain, inv)
    except Exception:
        specialist_results["geo-content-audit"] = {"status": "inconclusive", "findings": [], "recommendations": []}

    try:
        from engagement_check import audit as audit_eng
        extra = {"analytics": analytics} if analytics else None
        specialist_results["engagement-context-audit"] = run_specialist_sensor(audit_eng, base, domain, inv, extra)
    except Exception:
        specialist_results["engagement-context-audit"] = {"status": "inconclusive", "findings": [], "recommendations": []}

    return inv, specialist_results


def get_telemetry_payload(
    site: str,
    inventory: Optional[str] = None,
    analytics: Optional[str] = None,
    candidate_backlinks: Optional[str] = None,
) -> Dict[str, Any]:
    """Return raw empirical telemetry across all 6 sensors for AI cognitive orchestration."""
    base, domain = parse_target_domain(site)
    inv, specialist_results = collect_telemetry(site, inventory, analytics, candidate_backlinks)

    # Precompute Causal DAG state and suppression boundaries
    all_raw_findings: List[Dict[str, Any]] = []
    for _skill_name, result in specialist_results.items():
        all_raw_findings.extend(result.get("findings", []))

    has_layer0_block = any(
        (f.get("cause_id") or f.get("id", "")) in _LAYER0_CAUSE_IDS
        for f in all_raw_findings
    )
    has_layer1_rendering_gap = any(
        (f.get("cause_id") or f.get("id", "")) in _LAYER1_CAUSE_IDS
        for f in all_raw_findings
    )

    dag_root_causes: List[Dict[str, Any]] = []
    suppressed_categories: Set[str] = set()

    if has_layer0_block:
        dag_root_causes.append({
            "code": "AI_RETRIEVAL_BLOCKED",
            "scope": "site",
            "suppressed_categories": sorted(list(_SUPPRESSED_BY_LAYER0)),
            "rationale": "RFC 9309 search retrieval bot blocked or HTTP 4xx/5xx crawl failure preempts downstream evaluation.",
        })
        suppressed_categories.update(_SUPPRESSED_BY_LAYER0)

    if has_layer1_rendering_gap:
        dag_root_causes.append({
            "code": "RENDERED_CONTENT_GAP",
            "scope": "site",
            "suppressed_categories": sorted(list(_SUPPRESSED_BY_LAYER1)),
            "rationale": "Static plain text ratio below threshold with unhydrated SPA shell preempts citability and fact evaluation.",
        })
        suppressed_categories.update(_SUPPRESSED_BY_LAYER1)

    # Extract normalized sensor measurements
    disc_res = specialist_results.get("discoverability-audit", {})
    entity_res = specialist_results.get("entity-content-audit", {})
    fact_res = specialist_results.get("fact-consistency-audit", {})
    corrob_res = specialist_results.get("corroboration-authority-audit", {})
    geo_res = specialist_results.get("geo-content-audit", {})
    eng_res = specialist_results.get("engagement-context-audit", {})

    return {
        "site": site,
        "domain": domain,
        "crawled_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "archetype": detect_business_archetype(inv),
        "inventory": {
            "page_count": len(inv.get("pages", [])),
            "pages": [
                {
                    "url": p.get("url"),
                    "page_type": p.get("page_type"),
                    "word_count": p.get("word_count"),
                    "snr": p.get("snr"),
                }
                for p in inv.get("pages", [])
            ],
            "robots_summary": inv.get("robots", {}).get("summary", {}),
            "has_llms_txt": any("llms.txt" in (p.get("url") or "").lower() for p in inv.get("pages", [])),
        },
        "retrieval": {
            "robots_txt_found": bool(inv.get("robots")),
            "bot_matrix": disc_res.get("ai_agent_scrapeability_summary", {}).get("retrieval_bot_matrix", {}),
            "retrieval_bots_allowed": disc_res.get("coverage", {}).get("retrieval_bots_allowed"),
            "retrieval_bots_total": disc_res.get("coverage", {}).get("retrieval_bots_total"),
            "noindex_pages": [p.get("url") for p in inv.get("pages", []) if p.get("noindex")],
        },
        "rendering": {
            "visible_words_initial_html": disc_res.get("coverage", {}).get("visible_words_initial_html"),
            "spa_root_markers_detected": any(p.get("snr", 1.0) < 0.05 for p in inv.get("pages", [])),
        },
        "entity": {
            "jsonld_present": entity_res.get("coverage", {}).get("jsonld_present", False),
            "types_declared": entity_res.get("coverage", {}).get("types_declared", []),
            "sameas_declared": corrob_res.get("coverage", {}).get("sameas_declared", 0),
        },
        "facts": {
            "facts_checked": fact_res.get("coverage", {}).get("facts_checked", 0),
            "fact_conflicts": fact_res.get("coverage", {}).get("fact_conflicts", 0),
        },
        "corroboration": {
            "sameas_declared": corrob_res.get("coverage", {}).get("sameas_declared", 0),
            "sameas_resolvable": corrob_res.get("coverage", {}).get("sameas_resolvable", 0),
        },
        "geo": {
            "average_citability_score": geo_res.get("coverage", {}).get("average_citability_score"),
        },
        "engagement": {
            "pages_evaluated": eng_res.get("coverage", {}).get("pages_evaluated", 0),
        },
        "dag": {
            "has_layer0_block": has_layer0_block,
            "has_layer1_rendering_gap": has_layer1_rendering_gap,
            "root_causes": dag_root_causes,
            "suppressed_categories": sorted(list(suppressed_categories)),
        },
        "causal_state": {
            **(
                evaluate_epistemic_state(inv, specialist_results)
                if evaluate_epistemic_state is not None
                else {
                    "retrieval": "blocked" if has_layer0_block else "observed",
                    "rendering": "gap" if has_layer1_rendering_gap else "observed",
                    "entity": "observed",
                    "facts": "observed",
                    "corroboration": "observed",
                    "geo": "observed",
                    "engagement": "observed",
                }
            ),
            "nodes": (
                evaluate_causal_nodes(inv, specialist_results)
                if evaluate_causal_nodes is not None
                else {}
            ),
            "confirmed_root_causes": [c["code"] for c in dag_root_causes],
            "suppressed_checks": sorted(list(suppressed_categories)),
            "uncertainties": list(DEFAULT_LIMITATIONS),
        },
        "evidence_index": (
            build_evidence_index(inv, specialist_results)
            if build_evidence_index is not None
            else []
        ),
        "sensor_telemetry": specialist_results,
    }


def audit(
    site: str,
    inventory: Optional[str] = None,
    analytics: Optional[str] = None,
    candidate_backlinks: Optional[str] = None,
    state_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute end-to-end multi-skill brand AI-readiness audit."""
    inv, specialist_results = collect_telemetry(site, inventory, analytics, candidate_backlinks)

    # Cognitive Synthesis
    report = synthesize_audit_report(site, inv, specialist_results)

    # Validate against Draft-07 schema
    schema = load_schema()
    if schema and validate_type is not None:
        err = validate_type(report, schema)
        if err:
            sys.stderr.write(f"Schema Validation Error during audit synthesis: {err}\n")
            raise ValueError(f"Audit report failed Draft-07 schema validation: {err}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Master Orchestrator for Brand AI-Readiness & Visibility Audit."
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--inventory", help="Path to pre-crawled site inventory JSON (optional)")
    parser.add_argument("--candidate-backlinks", help="Path to candidate backlinks JSON (optional)")
    parser.add_argument("--analytics", help="Path to first-party analytics JSON (optional)")
    parser.add_argument("--output", help="Path to write final JSON report (optional, defaults to stdout)")
    parser.add_argument("--format", choices=["json"], default="json", help="Output format (default: json)")
    parser.add_argument("--telemetry", action="store_true", help="Output raw aggregated sensor telemetry for AI cognitive orchestration")

    args = parser.parse_args()

    try:
        if args.telemetry:
            payload = get_telemetry_payload(
                site=args.site,
                inventory=args.inventory,
                analytics=args.analytics,
                candidate_backlinks=args.candidate_backlinks,
            )
            formatted_output = json.dumps(payload, indent=2)
        else:
            report = audit(
                site=args.site,
                inventory=args.inventory,
                analytics=args.analytics,
                candidate_backlinks=args.candidate_backlinks,
            )
            formatted_output = json.dumps(report, indent=2)
    except Exception as e:
        sys.stderr.write(f"Orchestration Error: {e}\n")
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_output)
            f.write("\n")
        print(f"Audit report written to {args.output}")
    else:
        print(formatted_output)


if __name__ == "__main__":
    main()
