#!/usr/bin/env python3
"""
orchestrator.py - Master Orchestrator for Brand AI-Readiness & Visibility Audit.
Executes single-pass site acquisition, coordinates 6 specialist diagnostic sensors,
applies the full 6-layer Causal DAG and Keystone Defect deduplication, and emits a
strictly validated Draft-07 JSON report.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Canonical Retrieval Bot Set (RFC 9309 search retrieval bots only — NOT training)
# Blocking these is a critical/high defect. Blocking training bots (GPTBot,
# ClaudeBot) is a governance decision — NOT an AI search defect.
# ---------------------------------------------------------------------------
RETRIEVAL_BOTS: Set[str] = {"OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "anthropic-ai"}

# ---------------------------------------------------------------------------
# Archetype-Specific Severity Reweighting
# Scripts detect the archetype; AI contextualizes defect severity by business model.
# Source: knowledge-base.md Section 7 & 8
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

LABELS: Dict[str, str] = {
    "S4": "critical",
    "S3": "high",
    "S2": "medium",
    "S1": "low",
    "S0": "info",
    "U": "unassessable",
}


def calculate_priority_index(severity: int, difficulty: int) -> int:
    """Calculate task ranking index: priority_index = 5 * severity + (6 - difficulty)."""
    if not (1 <= severity <= 4):
        raise ValueError(f"severity must be in 1..4, got {severity}")
    if not (1 <= difficulty <= 5):
        raise ValueError(f"difficulty must be in 1..5, got {difficulty}")
    return 5 * severity + (6 - difficulty)


def infer_finding_difficulty(f: Dict[str, Any]) -> int:
    """Infer remediation difficulty (1=easiest, 5=hardest) from solution level or category."""
    d = f.get("difficulty")
    if isinstance(d, int) and 1 <= d <= 5:
        return d
    sol_level = str(f.get("solution_level", "")).upper()
    if sol_level == "E":  # Editorial copy update
        return 2
    if sol_level == "V":  # Mechanical validation / config / robots.txt
        return 2
    if sol_level == "C":  # Code / structured data / server template
        return 3
    if sol_level == "X":  # External platform claim / third-party profile
        return 4

    cat = str(f.get("category", "")).lower()
    cid = str(f.get("cause_id") or f.get("id") or "").lower()
    if "robots" in cat or "robots" in cid or "sitemap" in cid:
        return 2
    if "entity" in cat or "schema" in cat:
        return 2
    if "geo" in cat or "citability" in cat:
        return 2
    if "engagement" in cat:
        return 2
    if "fact" in cat or "drift" in cid:
        return 3
    if "corroboration" in cat or "authority" in cat or "backlink" in cid:
        return 4
    return 3


def resolve_dag_node(cid: str, cat: str) -> str:
    """Resolve exact Causal DAG layer (RETRIEVAL, RENDERING, ENTITY, FACTS, CORROBORATION, GEO_CITABILITY, ENGAGEMENT)."""
    cid_u = str(cid or "").upper()
    cat_l = str(cat or "").lower()

    # Support 134-item catalogue check prefixes (e.g. E1, D1, J1, C1, N10)
    if len(cid_u) <= 4 and cid_u and cid_u[0].isalpha():
        if cid_u.startswith("BN"):
            return "FACTS"
        if cid_u.startswith(("BC", "PP", "SA", "SC")):
            return "CORROBORATION"
        if cid_u.startswith(("EC", "ED", "ME")):
            return "ENTITY"
        if len(cid_u) <= 3 and (len(cid_u) == 1 or cid_u[1:].isdigit()):
            pfx = cid_u[0]
            if pfx in ("A", "B", "D", "H"):
                return "RETRIEVAL"
            if pfx == "C":
                return "RENDERING"
            if pfx == "E":
                return "ENTITY"
            if pfx == "F":
                return "FACTS"
            if pfx in ("G", "N"):
                return "GEO_CITABILITY"
            if pfx in ("I", "J"):
                return "ENGAGEMENT"
            if pfx == "P":
                return "CORROBORATION"

    # Layer 1: RENDERING
    if any(k in cid_u for k in ("RENDER", "HYDRAT", "SPA_SHELL", "UNRENDERED", "CSR_")):
        return "RENDERING"

    # Layer 0: RETRIEVAL
    if any(k in cid_u for k in ("RETRIEVAL", "ROBOTS", "NOINDEX", "SITEMAP", "CANONICAL", "HTTP_", "STATUS_", "REDIRECT", "LOCALE_", "CRAWL")):
        return "RETRIEVAL"
    if cat_l in ("crawlability", "discoverability", "indexability", "locale", "canonicalization", "http"):
        return "RETRIEVAL"

    # Layer 2: ENTITY
    if any(k in cid_u for k in ("ENTITY", "ORGANIZATION", "PRODUCT", "OFFER", "SCHEMA", "PRICE_METADATA", "LOCAL_BUSINESS", "SERVICE_SCHEMA", "COMMERCIAL_PRODUCT")):
        return "ENTITY"
    if cat_l in ("entity", "entity-identity", "structured-data", "structured_data", "commercial", "product-answerability", "entity-answerability", "schema-deprecation"):
        return "ENTITY"

    # Layer 3: FACTS
    if any(k in cid_u for k in ("CROSS_PAGE", "CONTRADICTION", "DISCREPANCY", "DRIFT", "STALE_YEAR", "TERMS_CONFLICT")):
        return "FACTS"
    if cat_l in ("fact-consistency", "fact_consistency", "facts", "lifecycle", "freshness", "commercial_terms", "representation"):
        return "FACTS"

    # Layer 4: CORROBORATION
    if any(k in cid_u for k in ("CORROBORATION", "SAMEAS", "AUTHORITY", "WIKIDATA", "WIKIPEDIA", "LINKEDIN", "ANCHOR", "MIRROR")):
        return "CORROBORATION"
    if cat_l in ("corroboration", "authority", "sameas"):
        return "CORROBORATION"

    # Layer 6: ENGAGEMENT
    if any(k in cid_u for k in ("ORIENTATION", "PROOF_ARCHITECTURE", "FRICTION", "OBJECTION", "PATHWAY", "CTA_", "SCENT", "BOUNCE", "VIEWPORT_ANSWER", "INTENT_TO_LANDING")):
        return "ENGAGEMENT"
    if cat_l in ("engagement", "conversion-continuity", "user-experience", "extraction"):
        return "ENGAGEMENT"

    # Layer 5: GEO_CITABILITY
    if any(k in cid_u for k in ("INFORMATION_GAIN", "QUOTATION", "MATRIX", "DEPTH", "CITABILITY", "FACT_TO_TOKEN", "FAQ_DEFICIT", "PASSAGE", "KEYWORD_DENSITY", "HEDGE", "BLUF", "EVIDENCE")):
        return "GEO_CITABILITY"
    if cat_l in ("geo_content", "geo-content", "content", "citability"):
        return "GEO_CITABILITY"

    return "RETRIEVAL"


def generate_priority_justification(f: Dict[str, Any], idx: int) -> str:
    """Generate needle-moving ordering judgment explaining why this finding is ranked at position #idx."""
    cid = str(f.get("cause_id") or f.get("id") or "").upper()
    dag = str(f.get("dag_node") or "RETRIEVAL")

    if cid in ("AI_RETRIEVAL_BLOCKED", "CRAWLER_ACCESS_DENIED"):
        just = "Keystone Layer 0 defect. Without HTTP 200 accessibility, AI retrieval engines cannot crawl or index pages, rendering all downstream markup and content invisible."
    elif "NOINDEX" in cid:
        just = "Explicit indexability blocker. The noindex directive instructs retrieval bots to purge the route from search indexes, superseding all on-page structured data and citability optimizations."
    elif "ROBOTS" in cid:
        just = "Crawler access barrier. Disallow directives on verified AI search bots prevent modern generative answer engines from retrieving the brand's primary domain content."
    elif "RENDER" in cid or dag == "RENDERING":
        just = "Layer 1 rendering failure. Serving an unrendered client-side JavaScript shell starves non-executing AI scrapers of text, preventing downstream entity extraction and neural dense retrieval."
    elif "MATERIAL_ENTITY_AMBIGUITY" in cid or "MISSING_ORGANIZATION" in cid:
        just = "Upstream entity anchor. Machine-explicit Schema.org Organization markup is required for LLMs to resolve brand identity and anchor facts in global knowledge graphs before citability can be attributed."
    elif "PRODUCT" in cid or "OFFER" in cid:
        just = "Commercial answerability blocker. Incomplete or unrendered product and pricing schemas prevent AI shopping assistants from providing direct buy recommendations and accurate price comparisons."
    elif "SAMEAS" in cid or "AUTHORITY" in cid or "KNOWLEDGE_GRAPH" in cid or dag == "CORROBORATION":
        just = "Knowledge graph consensus gap. Omitting established third-party authority profiles from Schema.org sameAs prevents AI models from verifying external consensus and corroborating brand claims."
    elif "CROSS_PAGE" in cid or "CONTRADICTION" in cid or dag == "FACTS":
        just = "Hallucination catalyst. Conflicting numerical or commercial claims across first-party pages directly depress RAG consensus confidence and cause generative engines to withhold definitive brand answers."
    elif "INFORMATION_GAIN" in cid:
        just = "Primary LLM citation filter. Content lacking proprietary data or empirical benchmarks is filtered out during generative answer synthesis because frontier models prioritize net-new information gain over generic summaries."
    elif "QUOTATION" in cid:
        just = "Citability multiplier. Grounded in Princeton KDD 2024 empirical benchmarks, attributed quotations from domain experts deliver a +40.9% lift in AI citation selection over unattributed assertions."
    elif "MATRIX" in cid or "COMPARATIVE" in cid:
        just = "High-lift retrieval structure. Princeton KDD 2024 benchmarks prove comparative tables yield the highest single empirical citation boost (+55.3%) for competitive brand queries."
    elif "FACT_TO_TOKEN" in cid:
        just = "RAG density deficit. Low atomic fact-to-token ratio causes dense retrieval algorithms to score passages as low-information fluff, routing queries to denser third-party references."
    elif "DEPTH" in cid:
        just = "Mechanistic depth gap. Generative engines favor sources explaining 'how' and 'why' through causal conjunctions over shallow assertions when answering complex user prompts."
    elif "ORIENTATION" in cid or "VALUE_PROPOSITION" in cid:
        just = "Post-citation bounce vector. Visitors arriving from specific AI citations bounce within 5 seconds when the hero section fails the cognitive orientation test with vague marketing abstractions."
    elif "PROOF" in cid:
        just = "Skepticism hurdle. AI search evaluators require quantitative benchmarks, enterprise logos, or compliance attestations immediately upon arrival to validate the factual claims made in the citation."
    elif "FRICTION" in cid or "GATE" in cid:
        just = "Conversion bottleneck. Forcing high-intent visitors arriving from citations into mandatory sales meetings without self-service sandbox exploration causes immediate referral abandonment."
    elif "PATHWAY" in cid:
        just = "Conversion cul-de-sac. Informational content concluding without logical conversion or exploration pathways strands interested visitors arriving from AI search."
    elif "CTA" in cid:
        just = "Intent continuity failure. Delaying primary action buttons behind auxiliary navigation blocks breaks the user task handoff initiated by the AI assistant citation."
    elif "LOCALE" in cid:
        just = "Multi-region retrieval mismatch. Invalid hreflang directives prevent search engines from routing localized queries to the correct regional brand assets."
    elif "FAQ" in cid:
        just = "Empirical citation penalty. Standalone conversational FAQs without underlying data points or technical specifications suffer a documented -5.7% citation penalty in generative engines."
    elif dag == "GEO_CITABILITY":
        just = "Deficit in statistical density, causal conjunctions, or BLUF primacy reduces heuristic citability score based on empirical GEO benchmarks."
    elif dag == "ENGAGEMENT":
        just = "Post-citation information scent or navigation friction indicates early-document orientation friction upon arrival from AI search."
    else:
        just = "Prioritized based on direct impact on AI retrieval visibility and user task continuity."

    return f"Rank #{idx}: {just}"


def plan(item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate disposition, queue, remedy readiness, and priority index for an audit item."""
    item = dict(item)
    level = rule.get("solution_level", "C")
    item["solution_level"] = level
    item["reference_band"] = rule.get("reference_band", "S2")
    item["benefit_area"] = {"G": ["geo"], "E": ["engagement"], "B": ["geo", "engagement"]}.get(
        rule.get("benefit_area", "G"), ["geo"]
    )
    kind = item.get("finding_kind", "confirmed_problem")
    if kind == "informational_observation":
        return item
    ready = item.get("remedy_readiness") == "ready"
    if level == "X":
        item.update(disposition="insufficient_evidence", remedy_readiness="not_possible")
        ready = False
    elif level == "E":
        item.update(disposition="editorial_draft", finding_kind="advisory")
    elif ready and level == "V" and item.get("candidate") and item.get("validation_results"):
        item["disposition"] = "validated_candidate"
    else:
        item["disposition"] = "conditional_proposal"
        item["remedy_readiness"] = "needs_context"
        ready = False
    if level == "C" and item.get("resolved_context") and item.get("validation_results") and item.get("suggested_action"):
        ready = True
        item["remedy_readiness"] = "ready"
    item["queue"] = "advisory" if item.get("finding_kind") == "advisory" else "confirmed" if ready else "investigation"
    item.setdefault("difficulty", None)
    item.setdefault("difficulty_range", None)
    item.setdefault("depends_on", [])
    if not ready:
        item["difficulty"] = None
    band = item.get("actual_band", "S2")
    d = item.get("difficulty")
    item["priority_index"] = (
        5 * int(band[1]) + (6 - d)
        if band in ("S1", "S2", "S3", "S4") and isinstance(d, int) and 1 <= d <= 5 and ready
        else None
    )
    if item.get("difficulty_range") and ready and band in ("S1", "S2", "S3", "S4"):
        lo, hi = item["difficulty_range"]
        item["priority_index_range"] = [5 * int(band[1]) + 6 - hi, 5 * int(band[1]) + 6 - lo]
    severity = LABELS.get(band, "medium")
    action = dict(item.get("suggested_action") or {})
    action.setdefault("summary", f"For {item.get('scope', '')}: {rule.get('solution', '')}")
    action.setdefault("technical_fix", f"Remediate {item.get('check_id', '')} according to technical specifications.")
    action.setdefault("creative_fix", None)
    action.setdefault("verification", "Inspect live response to confirm remediation.")
    action["priority"] = severity if severity in ("critical", "high", "medium", "low") else "medium"
    action.setdefault(
        "acceptance_tests",
        [
            "Recollect the exact cited scope after an owner-approved change.",
            "Verify the original predicate and unaffected contexts; no live change is applied by this audit.",
        ],
    )
    action.setdefault(
        "missing_context",
        []
        if ready
        else ["Owner intent, correct source values, implementation location and representative regression environment as specified in this check"],
    )
    item["suggested_action"] = action
    return item


try:
    from causal_gate import (
        DEFAULT_LIMITATIONS,
        LAYER0_CAUSE_IDS,
        LAYER1_CAUSE_IDS,
        ROOT_CAUSE_PRECEDENCE,
        SUPPRESSED_BY_LAYER0,
        SUPPRESSED_BY_LAYER1,
        TAXONOMY_ALIASES,
        apply_causal_suppression,
        build_evidence_index,
        compute_archetype_confidence,
        compute_severity_score,
        detect_business_archetype,
        evaluate_causal_nodes,
        evaluate_epistemic_state,
        extract_finding_route,
        normalize_route_path,
        routes_match,
        severity_from_score,
    )
except ImportError:
    try:
        from .causal_gate import (  # type: ignore
            DEFAULT_LIMITATIONS,
            LAYER0_CAUSE_IDS,
            LAYER1_CAUSE_IDS,
            ROOT_CAUSE_PRECEDENCE,
            SUPPRESSED_BY_LAYER0,
            SUPPRESSED_BY_LAYER1,
            TAXONOMY_ALIASES,
            apply_causal_suppression,
            build_evidence_index,
            compute_archetype_confidence,
            compute_severity_score,
            detect_business_archetype,
            evaluate_causal_nodes,
            evaluate_epistemic_state,
            extract_finding_route,
            normalize_route_path,
            routes_match,
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

        def detect_business_archetype(inv):  # type: ignore
            return "corporate"

        TAXONOMY_ALIASES = {
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
            "TEMPORAL_DRIFT_DETECTED": "CONTENT_RECENCY_DEFICIT",
            "CONTENT_RECENCY_DEFICIT": "TEMPORAL_DRIFT_DETECTED",
        }
        LAYER0_CAUSE_IDS = {
            "AI_RETRIEVAL_BLOCKED",
            "NOINDEX_EXCLUSION",
            "META_DIRECTIVE_CONFLICT",
            "ROBOTS_5XX_FAIL_CLOSED",
            "ROBOTS_TXT_OVERSIZED",
        }
        LAYER1_CAUSE_IDS = {
            "RENDERED_CONTENT_GAP",
            "NOSNIPPET_ON_CORE_CONTENT",
            "WAF_BOT_CHALLENGE",
            "CANONICAL_FRAGMENTATION",
            "CANONICAL_TARGET_MISMATCH",
        }
        SUPPRESSED_BY_LAYER0 = set()
        SUPPRESSED_BY_LAYER1 = set()

        def extract_finding_route(f: Dict[str, Any]) -> str:
            if not isinstance(f, dict):
                return ""
            url = f.get("url") or f.get("scope")
            if isinstance(url, dict):
                url = url.get("url") or url.get("scope") or ""
            if not url and isinstance(f.get("evidence"), dict):
                url = f["evidence"].get("scope") or ""
            if not url and isinstance(f.get("evidence"), str):
                m = re.search(r'https?://[^\s,\(\)\]"\']+', f["evidence"])
                if m:
                    url = m.group(0)
            return str(url or "").strip().lower()

        def normalize_route_path(route: str) -> str:
            if not route:
                return ""
            r = route.strip().lower()
            parsed = urlparse(r)
            path = parsed.path if parsed.scheme else r
            path = path.rstrip("/")
            return path if path else "/"

        def routes_match(r1: str, r2: str) -> bool:
            if not r1 or not r2:
                return False
            r1_norm = r1.strip().lower()
            r2_norm = r2.strip().lower()
            if r1_norm == r2_norm:
                return True
            p1 = normalize_route_path(r1)
            p2 = normalize_route_path(r2)
            if p1 != "/" and p2 != "/" and p1 == p2:
                return True
            if p1 != "/" and len(p1) > 2 and (p1 in r2_norm or r2_norm in p1):
                return True
            return bool(p2 != "/" and len(p2) > 2 and (p2 in r1_norm or r1_norm in p2))

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

_LAYER0_CAUSE_IDS = LAYER0_CAUSE_IDS
_LAYER1_CAUSE_IDS = LAYER1_CAUSE_IDS
_SUPPRESSED_BY_LAYER0 = SUPPRESSED_BY_LAYER0
_SUPPRESSED_BY_LAYER1 = SUPPRESSED_BY_LAYER1


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


def build_run_manifest(
    site: str,
    pipeline_stages: Optional[List[str]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    duration_seconds: float = 0.0,
    status: str = "complete",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a machine-readable execution provenance manifest recording site, timestamps, references, and validation status."""
    ref_dir = os.path.join(SCRIPT_DIR, "..", "references")
    reference_hashes = {}
    for ref_name in ("checks.json", "knowledge-base.md", "core-synthesis-digest.md", "report-schema.json", "telemetry-schema.json"):
        p = os.path.join(ref_dir, ref_name)
        if os.path.exists(p):
            with open(p, "rb") as rf:
                reference_hashes[ref_name] = hashlib.sha256(rf.read()).hexdigest()
        else:
            reference_hashes[ref_name] = None

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "manifest_version": "1.0.0",
        "site": site,
        "started_at": start_time or now_iso,
        "completed_at": end_time or now_iso,
        "duration_seconds": round(duration_seconds, 3),
        "execution_status": status,
        "pipeline_stages": pipeline_stages or [
            "1. Inventory Acquisition (SSRF-Safe, Pure Python)",
            "2. Specialist Telemetry Collection (6 Sensors)",
            "3. 6-Layer Causal DAG Suppression & Route Analysis",
            "4. Business Archetype Classification & Severity Reweighting",
            "5. Deterministic Readiness & Citability Scoring",
            "6. Draft-07 Report Synthesis & Schema Validation",
        ],
        "participating_skills": [
            "audit-orchestrator",
            "web-scraper",
            "discoverability-audit",
            "entity-content-audit",
            "fact-consistency-audit",
            "corroboration-authority-audit",
            "geo-content-audit",
            "engagement-context-audit",
        ],
        "reference_checksums_sha256": reference_hashes,
        "runtime_dependencies": "Pure Python 3.9+ standard library only",
    }
    if extra:
        manifest.update(extra)
    return manifest


def _build_default_proactive_actions(
    domain: str,
    brand_guess: str,
    route_refs: str,
    target_route: str,
    pricing_source: str,
    has_llms_txt: bool,
    finding_cids: Set[str],
    pages: List[Dict[str, Any]],
    unrendered_product_routes: Set[str],
    archetype: str,
    specialist_results: Dict[str, Dict[str, Any]],
    base: str,
) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    proactive_counter = 1

    # 1. Authoritative LLM Index Manifest (/llms.txt)
    if has_llms_txt:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Audit & Expand Existing /llms.txt Manifest for {brand_guess}",
            "category": "discoverability",
            "summary": f"Authoritative /llms.txt detected on {domain}. Audit section anchors and BLUF summaries to ensure comprehensive alignment with core guides.",
            "priority": "low",
            "technical_fix": f"Validate https://{domain}/llms.txt against llmstxt.org specification, linking directly to: {route_refs}.",
            "creative_fix": f"Author first-100-word executive overviews for every core {brand_guess} product and documentation guide.",
            "verification": f"Request GET https://{domain}/llms.txt and verify HTTP 200 with non-empty plain-text markdown.",
        })
        proactive_counter += 1
    else:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Deploy Machine-Readable /llms.txt Manifest for {brand_guess}",
            "category": "discoverability",
            "summary": f"Deploy an authoritative /llms.txt manifest at https://{domain}/llms.txt with BLUF summaries and clean markdown links for generative search assistants.",
            "priority": "low",
            "technical_fix": f"Serve /llms.txt at https://{domain}/llms.txt over HTTPS with Content-Type: text/plain and links to primary routes: {route_refs}.",
            "creative_fix": f"Author first-100-word executive overviews for every core {brand_guess} service guide.",
            "verification": f"Request GET https://{domain}/llms.txt and verify HTTP 200 with non-empty plain-text markdown.",
        })
        proactive_counter += 1

    # 2. Dynamic Edge Markdown Negotiation (Zero-token retrieval) if accessible and no rendering gap
    if "RENDERED_CONTENT_GAP" not in finding_cids and pages:
        actions.append({
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

    # Conditional Pre-Hydration Product Schema Architecture (when unrendered product shells were detected ON ECOMMERCE ROUTES ONLY)
    if unrendered_product_routes and archetype == "ecommerce" and pages:
        sample_routes = ", ".join(sorted(list(unrendered_product_routes))[:3])
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": "Pre-Hydration Product Schema Architecture",
            "category": "entity",
            "summary": (
                f"Commercial route(s) ({sample_routes}) serve unrendered client-side JS shells. "
                "When implementing SSR or pre-rendering, embed complete Schema.org Product and Offer markup "
                "(declaring name, description, offers with price, priceCurrency, and inStock availability) "
                "in the initial HTML document before client hydration to ensure instant discovery by AI shopping assistants."
            ),
            "priority": "high",
            "technical_fix": "Pre-render Schema.org Product JSON-LD in the server response before client bundle execution.",
            "creative_fix": "Ensure product title, description, pricing, and stock status are presented in semantic HTML above the fold.",
            "verification": "Fetch raw HTML without executing JavaScript and confirm Schema.org Product markup is present.",
        })
        proactive_counter += 1

    # 3. Archetype Strategic Enhancements (Only if NO corresponding defect exists and site is accessible)
    if archetype == "ecommerce" and "ATTRIBUTE_INCOMPLETENESS" not in finding_cids and not unrendered_product_routes and pages:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Implement Structured Specification Comparison Tables for {brand_guess}",
            "category": "entity",
            "summary": "Embed semantic HTML tables detailing product dimensions, materials, and origin to maximize conversational recommendations in ChatGPT Search and Perplexity.",
            "priority": "low",
            "technical_fix": f"Embed responsive HTML <table> markup on {target_route} with clean headers and numeric specifications.",
            "creative_fix": "Structure product feature specifications into quantitative rows (dimensions, materials, technical specifications, performance benchmarks).",
            "verification": f"Verify presence of semantic table elements in HTML of {target_route}.",
        })
        proactive_counter += 1
    elif archetype == "saas" and "FIRST_PARTY_FACT_CONFLICT" not in finding_cids and pages:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Deploy Autonomous AI Purchasing Agent Pricing Manifest (/pricing.md) for {brand_guess}",
            "category": "fact_consistency",
            "summary": "Expose an un-gated, machine-readable /pricing.md endpoint detailing plan tiers, token limits, seat costs, and API overage rates for autonomous AI purchasing agents.",
            "priority": "low",
            "technical_fix": f"Serve /pricing.md at https://{domain}/pricing.md with structured plan comparison tables extracted from {pricing_source}.",
            "creative_fix": f"Standardize plan names across {pricing_source} with transparent feature contrast rows.",
            "verification": f"Request GET https://{domain}/pricing.md and verify HTTP 200 with text/markdown Content-Type.",
        })
        proactive_counter += 1
    elif archetype == "publisher" and "MATERIAL_ENTITY_AMBIGUITY" not in finding_cids and pages:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Structure E-E-A-T Author Credentials & Fact Attributions for {brand_guess}",
            "category": "entity",
            "summary": f"Embed Schema.org Person markup for {brand_guess} editorial staff linking to verified LinkedIn/Wikidata profiles and structure 40–60 word BLUF answer blocks beneath question headings.",
            "priority": "low",
            "technical_fix": f"Embed Schema.org NewsArticle with Person authorship and sameAs links to external credential profiles on {base}/.",
            "creative_fix": "Replace passive voice with attributed expert quotes and verifiable benchmark statistics (+40.9% Princeton GEO lift).",
            "verification": f"Inspect article markup on https://{domain}/ with Google Rich Results Test to confirm valid Person credentials.",
        })
        proactive_counter += 1
    elif archetype == "local_business" and "MISSING_POSTAL_ADDRESS" not in finding_cids and pages:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Deploy MapGPT & Local AI Multi-Location Anchors for {brand_guess}",
            "category": "entity",
            "summary": "Structure Schema.org LocalBusiness with GeoCoordinates, openingHoursSpecification, and verified NAP consistency across all branch landing pages.",
            "priority": "low",
            "technical_fix": f"Embed Schema.org LocalBusiness with geo, telephone, openingHours, and priceRange on {base}/.",
            "creative_fix": f"Harmonize exact brand name '{brand_guess}', street address, and phone number formatting across local directory listings.",
            "verification": f"Inspect location page markup on https://{domain}/ with Google Rich Results Test.",
        })
        proactive_counter += 1
    elif "MATERIAL_ENTITY_AMBIGUITY" not in finding_cids and "WEAK_IDENTITY_SIGNALS" not in finding_cids and pages:
        corrob_res_p = specialist_results.get("corroboration-authority-audit") or {}
        corrob_cov_p = corrob_res_p.get("coverage") or {}
        p_sa_count = corrob_cov_p.get("sameas_declared", corrob_cov_p.get("sameas_count", 0)) or 0
        if p_sa_count > 0:
            actions.append({
                "id": f"P-{proactive_counter:03d}",
                "title": f"Expand Knowledge Graph Authority Anchors for {brand_guess}",
                "category": "corroboration",
                "summary": f"{brand_guess} currently declares {p_sa_count} sameAs node(s). Expand third-party authority coverage with Wikidata and LinkedIn verification.",
                "priority": "low",
                "technical_fix": f"Add verified Wikidata entity URI and official LinkedIn organization profile to Schema.org Organization on https://{domain}/.",
                "creative_fix": f"Maintain identical legal name '{brand_guess}' and contact details across all registered external profiles.",
                "verification": f"Inspect root HTML JSON-LD on https://{domain}/ with Google Rich Results Test or Schema.org Validator.",
            })
            proactive_counter += 1

    # 4. Princeton Citability Architecture (Only if citability defects are not already flagged and site is accessible)
    if not any(c in finding_cids for c in ("LOW_CITABILITY_SCORE", "LOW_FACT_TO_TOKEN_RATIO", "STANDALONE_FAQ_DEFICIT", "MISSING_IN_DEPTH_MECHANISMS")) and pages:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Implement Princeton KDD 2024 Citability Architecture on {domain}",
            "category": "geo_content",
            "summary": f"Structure core sections on {domain} into 134-167 word standalone passages under conversational question headings to maximize RAG snippet absorption.",
            "priority": "low",
            "technical_fix": f"Structure {domain} content under H2/H3 question headers with 40-60 word BLUF answers and semantic bullet lists.",
            "creative_fix": f"Eliminate exophoric pronouns in section leads ('It', 'They', 'We'); state canonical entity name '{brand_guess}' directly.",
            "verification": f"Audit {domain} section word counts and verify presence of causal conjunctions ('because', 'therefore', 'enables').",
        })
        proactive_counter += 1

    # 5. Upstream Crawler Whitelisting Action for Blocked / Unreachable sites
    if not pages:
        actions.append({
            "id": f"P-{proactive_counter:03d}",
            "title": f"Authorize Verified AI Search Crawlers in WAF & Edge Security for {brand_guess}",
            "category": "discoverability",
            "summary": f"Target host on {domain} blocked automated crawler probes during inventory acquisition. Configure edge security rules (Cloudflare, AWS WAF, Akamai) to permit verified AI retrieval engines.",
            "priority": "critical",
            "technical_fix": "Update WAF/CDN security policies to permit User-Agents: OAI-SearchBot, Claude-SearchBot, PerplexityBot with verified ASN IP validation.",
            "creative_fix": "Deploy challenge bypass rules for recognized AI retrieval bots rather than blanket interstitial blocks.",
            "verification": f"Probe {base}/ with OAI-SearchBot user-agent and confirm HTTP 200 is returned.",
        })
        proactive_counter += 1

    return actions


def synthesize_audit_report(
    site: str,
    inv: Dict[str, Any],
    specialist_results: Dict[str, Dict[str, Any]],
    review: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Apply Causal DAG, Keystone Defect deduplication, and Draft-07 synthesis."""
    base, domain = parse_target_domain(site)
    pages = inv.get("pages", []) if inv else []
    _domain_clean = domain.split(":")[0]
    _brand_guess = _domain_clean.split(".")[0].capitalize()

    # 1. Prefer brand from entity sensor snapshot if valid
    entity_brand = ((specialist_results.get("entity-content-audit") or {}).get("entity_snapshot") or {}).get("brand_name")
    if entity_brand and isinstance(entity_brand, str) and len(entity_brand.strip()) > 1:
        _brand_guess = entity_brand.strip()
    else:
        # 2. Inspect homepage specifically (root path or matching base)
        homepage_candidates = [
            p for p in pages
            if urlparse(p.get("url") or "").path in ("", "/", "/index.html")
            or (p.get("url") or "").rstrip("/") == base.rstrip("/")
            or p.get("page_type") == "homepage"
        ]
        target_pages = homepage_candidates if homepage_candidates else pages
        CHALLENGE_TITLE_PATTERNS = (
            "just a moment", "attention required", "security challenge", "security check",
            "access denied", "403 forbidden", "cloudflare", "ddos-guard", "robot or human",
            "verify you are human", "please enable javascript", "bot challenge", "checking your browser"
        )
        for p in target_pages:
            p_html = p.get("html") or ""
            m_og = re.search(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']', p_html, re.I)
            if m_og and m_og.group(1).strip():
                og_cand = m_og.group(1).strip()
                if not any(cp in og_cand.lower() for cp in CHALLENGE_TITLE_PATTERNS):
                    _brand_guess = og_cand
                    break
            m_title = re.search(r'<title[^>]*>([^<]+)</title>', p_html, re.I)
            if m_title and m_title.group(1).strip():
                t_raw = m_title.group(1).strip()
                if any(cp in t_raw.lower() for cp in CHALLENGE_TITLE_PATTERNS):
                    continue
                t_parts = re.split(r'[\s|:–—\-]+', t_raw)
                if t_parts and len(t_parts[0]) > 1 and not any(cp in t_parts[0].lower() for cp in CHALLENGE_TITLE_PATTERNS):
                    _brand_guess = t_parts[0].strip()
                    break

    # 3. Guard against generic / non-brand titles and challenge artifacts
    GENERIC_BRAND_BLACKLIST = {
        "signup", "sign up", "sign-up", "login", "log in", "log-in", "register",
        "home", "homepage", "index", "default", "welcome", "untitled", "test",
        "draft", "drafts", "cart", "checkout", "search", "products", "services",
        "about", "contact", "category", "account", "profile", "overview", "landing",
        "just", "moment", "attention", "required", "security", "challenge", "denied",
        "forbidden", "cloudflare", "just a moment...", "just a moment", "attention required!"
    }
    if _brand_guess.lower() in GENERIC_BRAND_BLACKLIST or len(_brand_guess) <= 1 or any(cp in _brand_guess.lower() for cp in ("just a moment", "attention required", "cloudflare")):
        _brand_guess = _domain_clean.split(".")[0].capitalize()

    sample_routes: List[str] = []
    sample_product_route = None
    sample_pricing_route = None
    EXCLUDED_ROUTE_PATTERNS = ("/drafts/", "/content/dam/", "/quiz/", "/assets/", "/static/", "/cdn-cgi/", "/_")
    for p in pages:
        if not isinstance(p, dict):
            continue
        p_url = p.get("url") or ""
        parsed_p = urlparse(p_url)
        path = parsed_p.path or "/"
        if (
            path not in ("/", "")
            and not any(ex in path.lower() for ex in EXCLUDED_ROUTE_PATTERNS)
            and not path.lower().endswith((".jpg", ".png", ".gif", ".svg", ".css", ".js"))
            and path not in sample_routes
        ):
            sample_routes.append(path)
        if (
            not sample_product_route
            and any(k in path.lower() for k in ("/product", "/products", "/item", "/items", "/shop", "/store", "/collection", "/collections", "/catalog", "/catalogue", "/goods"))
            and not any(ex in path.lower() for ex in EXCLUDED_ROUTE_PATTERNS)
        ):
            sample_product_route = path
        if (
            not sample_pricing_route
            and any(k in path.lower() for k in ("/pricing", "/plans", "/billing"))
            and not any(ex in path.lower() for ex in EXCLUDED_ROUTE_PATTERNS)
        ):
            sample_pricing_route = path

    has_llms_txt = any("llms.txt" in (p.get("url") or "").lower() for p in pages if isinstance(p, dict)) or bool(inv.get("llms_txt") if inv else False)

    all_raw_findings: List[Dict[str, Any]] = []
    all_raw_recommendations: List[Dict[str, Any]] = []

    statuses = []
    has_sensor_error = False
    for _skill_name, result in specialist_results.items():
        st = result.get("status", "ok")
        statuses.append(st)
        if st == "failed" or result.get("error"):
            has_sensor_error = True
        all_raw_findings.extend(result.get("findings", []))
        all_raw_recommendations.extend(result.get("recommendations", []))

    if review:
        rev_findings = []
        if isinstance(review, dict):
            rev_findings = review.get("findings") or review.get("candidates") or []
        elif isinstance(review, list):
            rev_findings = review
        if rev_findings:
            # When the AI Agent provides cognitive review findings, they become the primary findings
            all_raw_findings = [rf for rf in rev_findings if isinstance(rf, dict)]

    if inv.get("status") == "failed" or (not pages and not (inv.get("infrastructure") or {}).get("homepage_reachable", True)):
        audit_status = "failed"
    elif all(s == "ok" for s in statuses) and not has_sensor_error:
        audit_status = "complete"
    elif any(s in ("ok", "inconclusive", "failed") for s in statuses):
        audit_status = "partial"
    else:
        audit_status = "failed"

    # 1. Full 6-Layer Causal DAG Precedence Analysis & Keystone Defect Identification
    # (Source: knowledge-base.md Section 12)
    unrendered_product_routes: Set[str] = set()
    if apply_causal_suppression is not None:
        allowed_findings, suppressed_findings, dag_metadata = apply_causal_suppression(all_raw_findings, inv=inv)
        downstream_symptoms_by_cause = dag_metadata.get("downstream_symptoms", {})
        for sc in suppressed_findings:
            sym_cid = sc.get("cause_id") or sc.get("id") or ""
            if any(k in str(sym_cid) for k in ("ATTRIBUTE", "PRODUCT", "OFFER", "SCHEMA", "E")):
                sc_scope = extract_finding_route(sc)
                unrendered_product_routes.add(sc_scope or "commercial routes")
    else:
        allowed_findings = all_raw_findings
        downstream_symptoms_by_cause = {}

    # 2. Scope-Aware Deduplication of Findings
    deduped_findings: List[Dict[str, Any]] = []
    seen_dedup_keys: Set[str] = set()
    finding_counter = 1

    # Order by severity: critical -> high -> medium -> low
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    allowed_findings.sort(key=lambda f: severity_rank.get(f.get("severity", "low"), 1), reverse=True)

    for f in allowed_findings:
        cid = f.get("cause_id") or f.get("id") or f.get("title", "")

        # Deduplicate identical findings across routes by root cause and title (clean, non-mutating)
        dedup_key = f"{cid}::{f.get('title', '')}"
        if dedup_key in seen_dedup_keys:
            continue
        # Unify sameAs authority defect variants: keep one canonical anchor finding
        if cid in ("MISSING_SAMEAS_VERIFICATION", "UNLINKED_KNOWLEDGE_GRAPH_ANCHOR", "WEAK_IDENTITY_SIGNALS"):
            if "SAMEAS_DEFICIT" in seen_dedup_keys:
                continue
            seen_dedup_keys.add("SAMEAS_DEFICIT")
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

        raw_tf = action.get("technical_fix")
        if isinstance(raw_tf, dict):
            clean_tf = raw_tf
        else:
            clean_tf_str = clean_text_string(raw_tf) or None
            # Only format as sameAs if it is literally a raw stringified tuple of URLs on an authority finding
            if (
                clean_tf_str
                and clean_tf_str.strip().startswith(("('http", '("http'))
                and clean_tf_str.strip().endswith(("')", '")'))
                and any(k in cid for k in ("SAMEAS", "AUTHORITY", "CORROBORATION"))
            ):
                urls = re.findall(r"https?://[^\s'\"\)]+", clean_tf_str)
                if urls:
                    clean_tf_str = f"Update Organization JSON-LD on homepage to include 'sameAs': {json.dumps(urls[:5])}."
            clean_tf = clean_tf_str

        suggested_action: Dict[str, Any] = {
            "summary": action_summary,
            "technical_fix": clean_tf,
            "creative_fix": clean_text_string(action.get("creative_fix")) or None,
            "priority": action_priority,
            "verification": clean_text_string(action.get("verification")) or None,
            "is_proactive": bool(action.get("is_proactive", False)),
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
            "scope": f.get("scope") or f.get("url") or sample_url,
            "evidence": evidence_val,
            "impact": clean_text_string(raw_impact),
            "suggested_action": suggested_action,
        }

        if f.get("affected_urls"):
            clean_finding["affected_urls"] = list(f["affected_urls"])
        if prio_idx is not None:
            clean_finding["priority_index"] = prio_idx
        if f.get("depends_on"):
            clean_finding["depends_on"] = f["depends_on"]
        if f.get("downstream_symptoms"):
            clean_finding["downstream_symptoms"] = list(f["downstream_symptoms"])

        deduped_findings.append(clean_finding)

    # Attach downstream symptoms to keystone findings across all processed findings
    for clean_finding in deduped_findings:
        f_cid = clean_finding.get("cause_id") or clean_finding.get("id") or clean_finding.get("title", "")
        f_alias = TAXONOMY_ALIASES.get(f_cid, "")
        matching_symptoms = list(clean_finding.get("downstream_symptoms", []))
        for cause_k, syms in downstream_symptoms_by_cause.items():
            is_l1_match = (cause_k == "RENDERED_CONTENT_GAP" and (f_cid in _LAYER1_CAUSE_IDS or f_alias in _LAYER1_CAUSE_IDS))
            is_l0_match = (cause_k == "AI_RETRIEVAL_BLOCKED" and (f_cid in _LAYER0_CAUSE_IDS or f_alias in _LAYER0_CAUSE_IDS))
            if cause_k in (f_cid, f_alias) or TAXONOMY_ALIASES.get(cause_k) in (f_cid, f_alias) or is_l1_match or is_l0_match:
                for s in syms:
                    if s not in matching_symptoms:
                        matching_symptoms.append(s)
        if matching_symptoms:
            clean_finding["downstream_symptoms"] = matching_symptoms

    # 3. Archetype Detection, Severity Reweighting & Proactive Opportunities Synthesis
    if review and isinstance(review, dict) and review.get("archetype"):
        archetype = review["archetype"]
    else:
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

    # Re-sync actual_band, difficulty, and priority_index after archetype reweighting
    band_map = {"critical": "S4", "high": "S3", "medium": "S2", "low": "S1"}
    for finding in deduped_findings:
        finding["actual_band"] = band_map.get(finding.get("severity", "medium"), "S2")
        diff = finding.get("difficulty")
        if diff is None or not (isinstance(diff, int) and 1 <= diff <= 5):
            diff = infer_finding_difficulty(finding)
            finding["difficulty"] = diff
        p_idx = 5 * int(finding["actual_band"][1]) + (6 - diff)
        finding["priority_index"] = p_idx
        if finding.get("suggested_action"):
            finding["suggested_action"]["priority_index"] = p_idx
            finding["suggested_action"]["difficulty"] = diff

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

    # Synthesis of Keystone Layer 0 finding for blocked or unreachable crawls
    if not deduped_findings and not pages:
        crawl_limits = inv.get("limitations", []) if inv else []
        failure_note = crawl_limits[0] if crawl_limits else "Target web server or firewall blocked automated crawler requests (0 pages acquired)."
        blocked_finding = {
            "id": "F-001",
            "cause_id": "AI_RETRIEVAL_BLOCKED",
            "title": "Crawler access completely blocked by target host (0 pages acquired)",
            "severity": "critical",
            "category": "crawlability",
            "root_cause": f"Target host rejected or timed out automated crawler probes ({failure_note}), preventing AI search engines from indexing site content.",
            "confidence": "high",
            "scope": base,
            "evidence": {
                "summary": f"Single-pass inventory acquisition for {domain} acquired 0 usable HTML pages. {failure_note}",
                "sources": [
                    {
                        "url": f"{base}/",
                        "type": "http",
                        "observation": f"Automated crawl returned 0 pages. {failure_note}",
                    }
                ],
            },
            "impact": "Real-time AI search assistants (ChatGPT Search, Perplexity, Claude) cannot crawl, extract, or index any site content, causing total search engine invisibility.",
            "suggested_action": {
                "summary": "Configure WAF/CDN security rules to whitelist verified AI search crawlers and restore server accessibility.",
                "technical_fix": "Update WAF/firewall rules (Cloudflare, AWS WAF, Akamai) to allow verified AI search User-Agents (OAI-SearchBot, Claude-SearchBot, PerplexityBot) and ensure root URL returns HTTP 200.",
                "creative_fix": "Deploy targeted rate limiting instead of blanket IP or User-Agent challenge blocks for autonomous search assistance bots.",
                "priority": "critical",
                "verification": f"Probe {base}/ with honest audit user-agent and confirm HTTP 200 is returned with initial HTML.",
                "is_proactive": False,
                "priority_index": 20,
                "difficulty": 1,
            },
            "actual_band": "S3",
            "difficulty": 1,
            "priority_index": 20,
            "priority_rank": 1,
            "dag_node": "RETRIEVAL",
            "priority_justification": "Rank #1: Upstream barrier that completely blocks AI search engines from crawling, indexing, or extracting text across this route.",
            "affected_urls": [f"{base}/"],
        }
        deduped_findings = [blocked_finding]

    # Re-index finding IDs sequentially after sorting so final report has F-001, F-002, F-003...
    id_remap = {}
    for idx, f in enumerate(deduped_findings, 1):
        old_id = f.get("id")
        new_id = f"F-{idx:03d}"
        if old_id:
            id_remap[old_id] = new_id
        f["id"] = new_id
        f["priority_rank"] = idx

        # Compute DAG node per 6-Layer Causal DAG
        f_cid = str(f.get("cause_id") or "")
        f_cat = str(f.get("category") or "discoverability")
        f_dag = resolve_dag_node(f_cid, f_cat)
        f["dag_node"] = f_dag

        # Compute priority_justification explaining needle-moving rationale
        just = generate_priority_justification(f, idx)
        f["priority_justification"] = just

        if not f.get("affected_urls"):
            f["affected_urls"] = [f["scope"]] if f.get("scope") and str(f["scope"]).startswith("http") else [site]

        if f.get("suggested_action"):
            f["suggested_action"].setdefault("is_proactive", False)

    if id_remap:
        for f in deduped_findings:
            if f.get("depends_on"):
                f["depends_on"] = [id_remap.get(dep, dep) for dep in f["depends_on"]]

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
    if review and isinstance(review, dict) and review.get("proactive_actions"):
        for p_idx, pa in enumerate(review["proactive_actions"], 1):
            if isinstance(pa, dict) and pa.get("title") and pa.get("summary"):
                pa_clean = dict(pa)
                if not pa_clean.get("id"):
                    pa_clean["id"] = f"P-{p_idx:03d}"
                raw_prio = str(pa_clean.get("priority") or "medium").lower()
                pa_clean["priority"] = raw_prio if raw_prio in ("critical", "high", "medium", "low") else "medium"
                pa_clean["title"] = clean_text_string(pa_clean.get("title"))
                pa_clean["summary"] = clean_text_string(pa_clean.get("summary"))
                if pa_clean.get("category"):
                    pa_clean["category"] = clean_text_string(pa_clean["category"])
                if pa_clean.get("technical_fix"):
                    pa_clean["technical_fix"] = clean_text_string(pa_clean["technical_fix"])
                if pa_clean.get("creative_fix"):
                    pa_clean["creative_fix"] = clean_text_string(pa_clean["creative_fix"])
                if pa_clean.get("verification"):
                    pa_clean["verification"] = clean_text_string(pa_clean["verification"])
                proactive_actions.append(pa_clean)

    if not proactive_actions:
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

        # 2. Dynamic Edge Markdown Negotiation (Zero-token retrieval) if accessible and no rendering gap
        if "RENDERED_CONTENT_GAP" not in finding_cids and pages:
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

        # Conditional Pre-Hydration Product Schema Architecture (when unrendered product shells were detected ON ECOMMERCE ROUTES ONLY)
        if unrendered_product_routes and archetype == "ecommerce" and pages:
            sample_routes = ", ".join(sorted(list(unrendered_product_routes))[:3])
            proactive_actions.append({
                "id": f"P-{proactive_counter:03d}",
                "title": "Pre-Hydration Product Schema Architecture",
                "category": "entity",
                "summary": (
                    f"Commercial route(s) ({sample_routes}) serve unrendered client-side JS shells. "
                    "When implementing SSR or pre-rendering, embed complete Schema.org Product and Offer markup "
                    "(declaring name, description, offers with price, priceCurrency, and inStock availability) "
                    "in the initial HTML document before client hydration to ensure instant discovery by AI shopping assistants."
                ),
                "priority": "high",
                "technical_fix": "Pre-render Schema.org Product JSON-LD in the server response before client bundle execution.",
                "creative_fix": "Ensure product title, description, pricing, and stock status are presented in semantic HTML above the fold.",
                "verification": "Fetch raw HTML without executing JavaScript and confirm Schema.org Product markup is present.",
            })
            proactive_counter += 1

        # 3. Archetype Strategic Enhancements (Only if NO corresponding defect exists and site is accessible)
        if archetype == "ecommerce" and "ATTRIBUTE_INCOMPLETENESS" not in finding_cids and not unrendered_product_routes and pages:
            proactive_actions.append({
                "id": f"P-{proactive_counter:03d}",
                "title": f"Implement Structured Specification Comparison Tables for {_brand_guess}",
                "category": "entity",
                "summary": "Embed semantic HTML tables detailing product dimensions, materials, and origin to maximize conversational recommendations in ChatGPT Search and Perplexity.",
                "priority": "low",
                "technical_fix": f"Embed responsive HTML <table> markup on {target_route} with clean headers and numeric specifications.",
                "creative_fix": "Structure product feature specifications into quantitative rows (dimensions, materials, technical specifications, performance benchmarks).",
                "verification": f"Verify presence of semantic table elements in HTML of {target_route}.",
            })
            proactive_counter += 1
        elif archetype == "saas" and "FIRST_PARTY_FACT_CONFLICT" not in finding_cids and pages:
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
        elif archetype == "publisher" and "MATERIAL_ENTITY_AMBIGUITY" not in finding_cids and pages:
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
        elif archetype == "local_business" and "MISSING_POSTAL_ADDRESS" not in finding_cids and pages:
            proactive_actions.append({
                "id": f"P-{proactive_counter:03d}",
                "title": f"Deploy MapGPT & Local AI Multi-Location Anchors for {_brand_guess}",
                "category": "entity",
                "summary": "Structure Schema.org LocalBusiness with GeoCoordinates, openingHoursSpecification, and verified NAP consistency across all branch landing pages.",
                "priority": "low",
                "technical_fix": f"Embed Schema.org LocalBusiness with geo, telephone, openingHours, and priceRange on {base}/.",
                "creative_fix": f"Harmonize exact brand name '{_brand_guess}', street address, and phone number formatting across local directory listings.",
                "verification": f"Inspect location page markup on https://{domain}/ with Google Rich Results Test.",
            })
            proactive_counter += 1
        elif "MATERIAL_ENTITY_AMBIGUITY" not in finding_cids and "WEAK_IDENTITY_SIGNALS" not in finding_cids and pages:
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

        # 4. Princeton Citability Architecture (Only if citability defects are not already flagged and site is accessible)
        if not any(c in finding_cids for c in ("LOW_CITABILITY_SCORE", "LOW_FACT_TO_TOKEN_RATIO", "STANDALONE_FAQ_DEFICIT", "MISSING_IN_DEPTH_MECHANISMS")) and pages:
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

        # 5. Upstream Crawler Whitelisting Action for Blocked / Unreachable sites
        if not pages:
            proactive_actions.append({
                "id": f"P-{proactive_counter:03d}",
                "title": f"Authorize Verified AI Search Crawlers in WAF & Edge Security for {_brand_guess}",
                "category": "discoverability",
                "summary": f"Target host on {domain} blocked automated crawler probes during inventory acquisition. Configure edge security rules (Cloudflare, AWS WAF, Akamai) to permit verified AI retrieval engines.",
                "priority": "critical",
                "technical_fix": "Update WAF/CDN security policies to permit User-Agents: OAI-SearchBot, Claude-SearchBot, PerplexityBot with verified ASN IP validation.",
                "creative_fix": "Deploy challenge bypass rules for recognized AI retrieval bots rather than blanket interstitial blocks.",
                "verification": f"Probe {base}/ with OAI-SearchBot user-agent and confirm HTTP 200 is returned.",
            })
            proactive_counter += 1

    final_proactive = proactive_actions[:3]
    for idx, act in enumerate(final_proactive, start=1):
        act["id"] = f"P-{idx:03d}"

    # 4. Counts-by-Severity Summary (computed earlier after archetype reweighting)
    # (crit_count, high_count, med_count, low_count already set above)

    # 5. Deterministic Readiness Score & Dimensions Breakdown
    pages_list = inv.get("pages", []) if inv else []
    total_pages = max(len(pages_list), 1)

    if pages_list:
        def _to_code(p_item):
            c = p_item.get("status_code") or p_item.get("status")
            try:
                val = int(c)
                return val if 100 <= val <= 599 else None
            except (ValueError, TypeError):
                return None
        crawlable_count = sum(1 for p in pages_list if _to_code(p) is not None and _to_code(p) < 400)
        crawlability = round((crawlable_count / total_pages) * 100.0, 2) if total_pages > 0 else 0.0
    else:
        crawlability = 0.0

    disc_cov = specialist_results.get("discoverability-audit", {}).get("coverage", {})
    substantive_pages = [
        p for p in pages_list
        if (p.get("word_count", 0) or 0) >= 50
        and not any(k in (p.get("url") or "").lower() for k in ("/footer", "/nav", "/draft", "/fragment"))
    ]
    retrieval_readiness = round((len(substantive_pages) / total_pages) * 100.0, 2) if pages_list else 0.0

    geo_cov = specialist_results.get("geo-content-audit", {}).get("coverage", {})
    avg_cit = geo_cov.get("average_citability_score", 0.0)
    citation_readiness = round(float(avg_cit or 0.0), 2)

    entity_cov = specialist_results.get("entity-content-audit", {}).get("coverage", {})
    corrob_cov = specialist_results.get("corroboration-authority-audit", {}).get("coverage", {})
    has_jsonld = bool(entity_cov.get("jsonld_present", False))
    has_org = bool(specialist_results.get("entity-content-audit", {}).get("entity_snapshot", {}).get("organization"))
    sameas_count = int(corrob_cov.get("sameas_declared", 0) or 0)
    if has_jsonld and has_org and sameas_count >= 2:
        entity_authority = 100.0
    elif has_jsonld or has_org:
        entity_authority = 50.0
    elif sameas_count > 0:
        entity_authority = 25.0
    else:
        entity_authority = 0.0

    raw_bots_allowed = disc_cov.get("retrieval_bots_allowed")
    bots_allowed = int(raw_bots_allowed) if raw_bots_allowed is not None else 4
    raw_bots_total = disc_cov.get("retrieval_bots_total")
    bots_total = max(int(raw_bots_total) if raw_bots_total is not None else 4, 1)
    bot_ratio = bots_allowed / bots_total if bots_total else 1.0
    cross_engine_visibility = round(bot_ratio * retrieval_readiness, 2)

    def _is_commerce_page(p_item):
        u = str(p_item.get("url") or "").lower()
        if any(k in u for k in ("/product/", "/pricing", "/cart", "/checkout", "/shop")):
            return True
        pt = p_item.get("page_type")
        if isinstance(pt, dict):
            pt = pt.get("value")
        pt_str = str(pt or "").lower()
        return pt_str in ("product", "pricing", "catalog", "product_detail")

    commerce_pages = sum(1 for p in pages_list if _is_commerce_page(p))
    agentic_commerce = round((commerce_pages / total_pages) * 100.0, 2) if pages_list else 0.0

    dimensions = {
        "crawlability": crawlability,
        "retrieval_readiness": retrieval_readiness,
        "citation_readiness": citation_readiness,
        "entity_authority": entity_authority,
        "cross_engine_visibility": cross_engine_visibility,
        "agentic_commerce": agentic_commerce,
    }
    weights = {
        "crawlability": 0.2,
        "retrieval_readiness": 0.15,
        "citation_readiness": 0.25,
        "entity_authority": 0.2,
        "cross_engine_visibility": 0.1,
        "agentic_commerce": 0.1,
    }
    composite_score = round(sum(dimensions[k] * weights[k] for k in weights), 2)
    if composite_score >= 85.0:
        grade = "A"
    elif composite_score >= 70.0:
        grade = "B"
    elif composite_score >= 50.0:
        grade = "C"
    elif composite_score >= 30.0:
        grade = "D"
    else:
        grade = "F"

    dimension_status = {
        "crawlability": "observed" if pages_list else "unmeasured",
        "retrieval_readiness": "observed" if pages_list else "unmeasured",
        "citation_readiness": "provisional" if "RENDERED_CONTENT_GAP" in finding_cids else "observed",
        "entity_authority": "provisional" if "RENDERED_CONTENT_GAP" in finding_cids else "observed",
        "cross_engine_visibility": "observed" if pages_list else "unmeasured",
        "agentic_commerce": "provisional" if "RENDERED_CONTENT_GAP" in finding_cids else "observed",
    }

    readiness = {
        "composite_score": composite_score,
        "grade": grade,
        "dimensions": dimensions,
        "weights": weights,
        "dimension_status": dimension_status,
        "score_scope": "Observed static inventory and specialist telemetry; heuristic citation-readiness proxy, not live provider ranking or citation measurement.",
    }

    # 6. Assemble Final Draft-07 Compliant Report (Signal Only, Zero Bloat)
    report: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "site": site,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "audit_status": audit_status,
        "archetype": archetype,
        "summary": {
            "total_findings": len(deduped_findings),
            "critical": crit_count,
            "high": high_count,
            "medium": med_count,
            "low": low_count,
            "detected_archetype": archetype,
        },
        "findings": deduped_findings,
        "proactive_actions": final_proactive,
        "readiness": readiness,
        "coverage": {
            "pages_crawled": len(pages_list),
            "specialist_domains": len(specialist_results),
            "sensor_errors": [
                k for k, v in specialist_results.items()
                if (v.get("status") in ("inconclusive", "failed") and v.get("error")) or v.get("status") == "failed"
            ],
        },
        "limitations": [
            "No JavaScript browser rendering was performed.",
            "Findings are based only on resources successfully acquired during this audit.",
            "Robots.txt observations represent declared crawler permissions and do not prove search inclusion, indexing, ranking, or citation.",
            "No claim is made about actual citation or placement by a specific AI assistant.",
            "Engagement observations are content/navigation proxies unless external behavioral analytics are explicitly supplied.",
        ],
    }

    geo_res = specialist_results.get("geo-content-audit", {})
    if geo_res.get("geo_citability_summary"):
        report["geo_citability_summary"] = geo_res["geo_citability_summary"]
    if geo_res.get("page_improvement_plans"):
        for pip in geo_res["page_improvement_plans"]:
            if isinstance(pip, dict) and not pip.get("page_type"):
                pip["page_type"] = "general"
        report["page_improvement_plans"] = geo_res["page_improvement_plans"]

    eng_res = specialist_results.get("engagement-context-audit", {})
    if eng_res.get("engagement_continuity_summary"):
        report["engagement_continuity_summary"] = eng_res["engagement_continuity_summary"]

    scrape_summary = (inv.get("infrastructure") or {}).get("ai_agent_scrapeability_summary") or (specialist_results.get("discoverability-audit") or {}).get("ai_agent_scrapeability_summary")
    if scrape_summary:
        report["ai_agent_scrapeability_summary"] = scrape_summary

    if suppressed_findings:
        report["suppressed_findings"] = suppressed_findings

    run_manifest = build_run_manifest(site=site)
    report["run_manifest"] = run_manifest
    report["coverage"]["run_manifest"] = run_manifest

    return report


def collect_telemetry(
    site: str,
    inventory: Optional[str] = None,
    analytics: Optional[str] = None,
    candidate_backlinks: Optional[str] = None,
    responses: Optional[str] = None,
    skills: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Acquire inventory and execute specialist sensors, returning (inv, specialist_results)."""
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

    specialist_results: Dict[str, Dict[str, Any]] = {}

    skill_filter = None
    if skills:
        skill_alias_map = {
            "discoverability": "discoverability-audit",
            "discoverability-audit": "discoverability-audit",
            "entity": "entity-content-audit",
            "entity-content": "entity-content-audit",
            "entity-content-audit": "entity-content-audit",
            "fact": "fact-consistency-audit",
            "fact-consistency": "fact-consistency-audit",
            "fact-consistency-audit": "fact-consistency-audit",
            "corroboration": "corroboration-authority-audit",
            "corroboration-authority": "corroboration-authority-audit",
            "corroboration-authority-audit": "corroboration-authority-audit",
            "authority": "corroboration-authority-audit",
            "geo": "geo-content-audit",
            "geo-content": "geo-content-audit",
            "geo-content-audit": "geo-content-audit",
            "engagement": "engagement-context-audit",
            "engagement-context": "engagement-context-audit",
            "engagement-context-audit": "engagement-context-audit",
        }
        skill_filter = set()
        for s in skills:
            s_clean = s.strip().lower()
            canonical = skill_alias_map.get(s_clean)
            if canonical:
                skill_filter.add(canonical)
            else:
                if not s_clean.endswith("-audit"):
                    s_clean += "-audit"
                skill_filter.add(s_clean)

    # Guard: If inventory failed (network down / site blocked), emit inconclusive
    if inv.get("status") == "failed" or not inv.get("pages"):
        active_skills = [
            "discoverability-audit",
            "entity-content-audit",
            "fact-consistency-audit",
            "corroboration-authority-audit",
            "geo-content-audit",
            "engagement-context-audit",
        ]
        if skill_filter is not None:
            active_skills = [s for s in active_skills if s in skill_filter]
        for skill_id in active_skills:
            specialist_results[skill_id] = {
                "status": "inconclusive",
                "findings": [],
                "recommendations": [],
                "error": inv.get("error"),
            }
        return inv, specialist_results

    if skill_filter is None or "discoverability-audit" in skill_filter:
        try:
            from discoverability_check import audit as audit_disc
            specialist_results["discoverability-audit"] = run_specialist_sensor(audit_disc, base, domain, inv)
        except Exception as e:
            specialist_results["discoverability-audit"] = {"status": "failed", "error": f"Sensor load exception: {type(e).__name__}: {e}", "findings": [], "recommendations": []}

    if skill_filter is None or "entity-content-audit" in skill_filter:
        try:
            from entity_content_check import audit as audit_entity
            specialist_results["entity-content-audit"] = run_specialist_sensor(audit_entity, base, domain, inv)
        except Exception as e:
            specialist_results["entity-content-audit"] = {"status": "failed", "error": f"Sensor load exception: {type(e).__name__}: {e}", "findings": [], "recommendations": []}

    if skill_filter is None or "fact-consistency-audit" in skill_filter:
        try:
            from fact_consistency_check import audit as audit_fact
            extra = {"responses_file": responses} if responses else None
            specialist_results["fact-consistency-audit"] = run_specialist_sensor(audit_fact, base, domain, inv, extra)
        except Exception as e:
            specialist_results["fact-consistency-audit"] = {"status": "failed", "error": f"Sensor load exception: {type(e).__name__}: {e}", "findings": [], "recommendations": []}

    if skill_filter is None or "corroboration-authority-audit" in skill_filter:
        try:
            from corroboration_check import audit as audit_corrob
            extra = {"candidate_backlinks": candidate_backlinks} if candidate_backlinks else None
            specialist_results["corroboration-authority-audit"] = run_specialist_sensor(audit_corrob, base, domain, inv, extra)
        except Exception as e:
            specialist_results["corroboration-authority-audit"] = {"status": "failed", "error": f"Sensor load exception: {type(e).__name__}: {e}", "findings": [], "recommendations": []}

    if skill_filter is None or "geo-content-audit" in skill_filter:
        try:
            from geo_content_check import audit as audit_geo
            specialist_results["geo-content-audit"] = run_specialist_sensor(audit_geo, base, domain, inv)
        except Exception as e:
            specialist_results["geo-content-audit"] = {"status": "failed", "error": f"Sensor load exception: {type(e).__name__}: {e}", "findings": [], "recommendations": []}

    if skill_filter is None or "engagement-context-audit" in skill_filter:
        try:
            from engagement_check import audit as audit_eng
            extra = {"analytics": analytics} if analytics else None
            specialist_results["engagement-context-audit"] = run_specialist_sensor(audit_eng, base, domain, inv, extra)
        except Exception as e:
            specialist_results["engagement-context-audit"] = {"status": "failed", "error": f"Sensor load exception: {type(e).__name__}: {e}", "findings": [], "recommendations": []}

    return inv, specialist_results


def get_telemetry_payload(
    site: str,
    inventory: Optional[str] = None,
    analytics: Optional[str] = None,
    candidate_backlinks: Optional[str] = None,
    responses: Optional[str] = None,
    skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Return raw empirical telemetry across specialist sensors for AI cognitive orchestration."""
    base, domain = parse_target_domain(site)
    inv, specialist_results = collect_telemetry(
        site, inventory, analytics, candidate_backlinks, responses=responses, skills=skills
    )

    # Precompute Causal DAG state and suppression boundaries
    all_raw_findings: List[Dict[str, Any]] = []
    for _skill_name, result in specialist_results.items():
        all_raw_findings.extend(result.get("findings", []))

    has_layer0_block = any(
        (f.get("cause_id") or f.get("id", "")) in _LAYER0_CAUSE_IDS
        or TAXONOMY_ALIASES.get(f.get("cause_id") or f.get("id", ""), "") in _LAYER0_CAUSE_IDS
        for f in all_raw_findings
    )
    has_layer1_rendering_gap = any(
        (f.get("cause_id") or f.get("id", "")) in _LAYER1_CAUSE_IDS
        or TAXONOMY_ALIASES.get(f.get("cause_id") or f.get("id", ""), "") in _LAYER1_CAUSE_IDS
        for f in all_raw_findings
    )

    dag_root_causes: List[Dict[str, Any]] = []
    suppressed_categories: Set[str] = set()

    if apply_causal_suppression is not None:
        _allowed, _suppressed, dag_meta = apply_causal_suppression(all_raw_findings, inv=inv)
        dag_root_causes = dag_meta.get("root_causes", [])
        suppressed_categories = set(dag_meta.get("suppressed_categories", []))
    else:
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

    pages_list = inv.get("pages", []) if inv else []
    enriched_pages = []
    for p in pages_list:
        p_html = p.get("html") or ""
        p_title = p.get("title")
        if isinstance(p_title, list):
            p_title = clean_text_string(p_title[0]) if p_title else None
        elif p_title:
            p_title = clean_text_string(p_title)
        elif p_html:
            m_t = re.search(r"<title[^>]*>([^<]+)</title>", p_html, re.I)
            if m_t:
                p_title = clean_text_string(m_t.group(1))

        p_h1 = p.get("h1")
        if isinstance(p_h1, list):
            p_h1 = clean_text_string(p_h1[0]) if p_h1 else None
        elif p_h1:
            p_h1 = clean_text_string(p_h1)
        elif p_html:
            m_h = re.search(r"<h1[^>]*>([^<]+)</h1>", p_html, re.I)
            if m_h:
                p_h1 = clean_text_string(m_h.group(1))

        has_jld = bool(p.get("json_ld_contents")) or ("application/ld+json" in p_html)
        enriched_pages.append({
            "url": p.get("url"),
            "status": p.get("status_code") or p.get("status") or "unknown",
            "page_type": p.get("page_type"),
            "title": p_title,
            "h1": p_h1,
            "word_count": p.get("word_count"),
            "snr": round(float(p.get("snr", 0.0)), 3) if p.get("snr") is not None else None,
            "canonical": p.get("canonical"),
            "has_jsonld": has_jld,
            "ctas_count": len(p.get("ctas", [])),
            "has_hreflang": bool(p.get("hreflangs")),
            "dates": p.get("dates", {}),
        })

    sitemaps_list = inv.get("sitemaps", []) if inv else []
    status_counts: Dict[str, int] = {}
    pages_by_type: Dict[str, int] = {}
    for p in pages_list:
        code_str = str(p.get("status_code") or p.get("status") or "unknown")
        status_counts[code_str] = status_counts.get(code_str, 0) + 1
        pt = str(p.get("page_type") or "other")
        pages_by_type[pt] = pages_by_type.get(pt, 0) + 1

    avg_wc = round(sum(p.get("word_count", 0) or 0 for p in pages_list) / max(len(pages_list), 1), 1)
    avg_snr = round(sum(float(p.get("snr", 0.0) or 0.0) for p in pages_list) / max(len(pages_list), 1), 3)
    thin_pages = [p.get("url") for p in pages_list if (p.get("word_count", 0) or 0) < 50 and p.get("url")]

    return {
        "site": site,
        "domain": domain,
        "crawled_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "archetype": detect_business_archetype(inv),
        "inventory": {
            "page_count": len(pages_list),
            "pages": enriched_pages,
            "robots_summary": (inv.get("robots") or {}).get("summary") or {},
            "sitemaps_count": len(sitemaps_list),
            "sitemaps": [s if isinstance(s, str) else s.get("loc", "") for s in sitemaps_list[:10] if isinstance(s, (str, dict))],
            "has_llms_txt": any("llms.txt" in (p.get("url") or "").lower() for p in pages_list if isinstance(p, dict)),
        },
        "crawl_telemetry": {
            "pages_crawled": len(pages_list),
            "average_latency_ms": (inv.get("performance") or {}).get("average_latency_ms"),
            "total_facts_extracted": (inv.get("performance") or {}).get("total_facts", 0),
            "total_claims_extracted": (inv.get("performance") or {}).get("total_claims", 0),
            "pages_by_type": pages_by_type,
            "total_ctas_extracted": sum(len(p.get("ctas", [])) for p in pages_list if isinstance(p, dict)),
            "pages_with_hreflang": sum(1 for p in pages_list if isinstance(p, dict) and p.get("hreflangs")),
        },
        "retrieval": {
            "robots_txt_found": bool(inv.get("robots")),
            "bot_matrix": (disc_res.get("ai_agent_scrapeability_summary") or {}).get("retrieval_bot_matrix") or {},
            "retrieval_bots_allowed": (disc_res.get("coverage") or {}).get("retrieval_bots_allowed"),
            "retrieval_bots_total": (disc_res.get("coverage") or {}).get("retrieval_bots_total"),
            "noindex_pages": [p.get("url") for p in pages_list if isinstance(p, dict) and p.get("noindex")],
            "has_ai_plugin": bool(((inv.get("infrastructure") or {}).get("ai_plugin") or {}).get("present")),
            "has_security_txt": bool(((inv.get("infrastructure") or {}).get("security_txt") or {}).get("present")),
            "has_llms_txt": bool(((inv.get("infrastructure") or {}).get("llms_txt") or {}).get("present")) or any("llms.txt" in (p.get("url") or "").lower() for p in pages_list if isinstance(p, dict)),
            "has_pricing_md": bool(
                ((inv.get("infrastructure") or {}).get("pricing_manifest") or (inv.get("infrastructure") or {}).get("pricing_md") or {}).get("present")
            ),
            "sitemaps_found": len(sitemaps_list),
            "status_distribution": status_counts,
        },
        "rendering": {
            "visible_words_initial_html": (disc_res.get("coverage") or {}).get("visible_words_initial_html"),
            "spa_root_markers_detected": any(float(p.get("snr") or 1.0) < 0.05 for p in pages_list if isinstance(p, dict)),
            "average_word_count": avg_wc,
            "average_snr": avg_snr,
            "average_page_snr": avg_snr,
            "thin_content_pages": thin_pages,
        },
        "entity": {
            "jsonld_present": entity_res.get("coverage", {}).get("jsonld_present", False),
            "types_declared": entity_res.get("coverage", {}).get("types_declared", []),
            "sameas_declared": corrob_res.get("coverage", {}).get("sameas_declared", 0),
            "organization_detected": entity_res.get("entity_snapshot", {}).get("brand_name"),
            "org_schema_present": bool(entity_res.get("entity_snapshot", {}).get("organization")),
            "product_schema_pages": entity_res.get("coverage", {}).get("product_schema_pages", 0),
            "answerability_evaluations": entity_res.get("coverage", {}).get("answerability_evaluations", []),
        },
        "facts": {
            "facts_checked": fact_res.get("coverage", {}).get("facts_checked", 0),
            "fact_conflicts": fact_res.get("coverage", {}).get("fact_conflicts", 0),
            "scoped_facts_recorded": fact_res.get("coverage", {}).get("scoped_facts_recorded", 0),
            "conflicts_detected": [
                f.get("title") for f in fact_res.get("findings", [])
                if f.get("cause_id") in (
                    "FIRST_PARTY_FACT_CONFLICT",
                    "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
                    "DISCONTINUED_VS_CURRENT_CONFLICT",
                    "CONFLICTING_COMMERCIAL_TERMS",
                )
            ],
        },
        "corroboration": {
            "sameas_declared": corrob_res.get("coverage", {}).get("sameas_declared", 0),
            "sameas_resolvable": corrob_res.get("coverage", {}).get("sameas_resolvable", 0),
            "candidate_backlinks_provided": corrob_res.get("coverage", {}).get("candidate_backlinks_provided", 0),
            "candidate_backlinks_verified": corrob_res.get("coverage", {}).get("candidate_backlinks_verified", 0),
            "broken_authority_anchors": [
                f.get("title") for f in corrob_res.get("findings", [])
                if f.get("cause_id") == "BROKEN_AUTHORITY_ANCHOR"
            ],
        },
        "geo": {
            "average_citability_score": geo_res.get("coverage", {}).get("average_citability_score"),
            "pages_evaluated": len(geo_res.get("page_improvement_plans", [])) or geo_res.get("coverage", {}).get("target_pages_evaluated", 0),
            "target_citability_score": 80,
            "evidence_genres_distribution": geo_res.get("geo_citability_summary", {}).get("evidence_genres_distribution", {}),
            "information_gain_deficits": [
                f.get("url") for f in geo_res.get("findings", [])
                if f.get("cause_id") == "INFORMATION_GAIN_DEFICIT"
            ],
            "authority_quotation_gaps": [
                f.get("url") for f in geo_res.get("findings", [])
                if f.get("cause_id") == "PRIMARY_AUTHORITY_QUOTATION_GAP"
            ],
            "comparative_matrix_gaps": [
                f.get("url") for f in geo_res.get("findings", [])
                if f.get("cause_id") == "COMPARATIVE_ANSWERABILITY_MATRIX"
            ],
            "lowest_scoring_pages": [
                {
                    "url": pip.get("url") or pip.get("page_url") or "",
                    "citability_score": pip.get("citability_score", 0),
                }
                for pip in sorted(geo_res.get("page_improvement_plans", []), key=lambda x: x.get("citability_score", 0))[:5]
            ],
        },
        "engagement": {
            "pages_evaluated": eng_res.get("coverage", {}).get("pages_evaluated", 0),
            "h1_aligned_pages": eng_res.get("coverage", {}).get("h1_aligned_pages", 0),
            "cta_above_fold_pages": eng_res.get("coverage", {}).get("cta_above_fold_pages", 0),
            "orientation_clarity_score": eng_res.get("engagement_continuity_summary", {}).get("average_information_scent_score", 1.0),
            "cta_reachability_score": eng_res.get("engagement_continuity_summary", {}).get("average_cta_reachability_score", 1.0),
            "proof_architecture_deficits": [
                f.get("url") for f in eng_res.get("findings", [])
                if f.get("cause_id") == "PROOF_ARCHITECTURE_DEFICIT"
            ],
            "orientation_vacuums": [
                f.get("url") for f in eng_res.get("findings", [])
                if f.get("cause_id") in ("VALUE_PROPOSITION_ORIENTATION_VACUUM", "LOW_INFORMATION_SCENT", "GENERIC_H1")
            ],
            "friction_barriers": [
                f.get("url") for f in eng_res.get("findings", [])
                if f.get("cause_id") in ("FRICTION_TO_VALUE_BARRIER", "CTA_REACHABILITY_FRICTION")
            ],
            "objection_coverage_voids": [
                f.get("url") for f in eng_res.get("findings", [])
                if f.get("cause_id") == "OBJECTION_COVERAGE_VOID"
            ],
            "dead_end_routes": [
                f.get("url") for f in eng_res.get("findings", [])
                if f.get("cause_id") == "DECISION_PATHWAY_DEAD_END"
            ],
            "generic_h1_pages": [
                f.get("url") for f in eng_res.get("findings", [])
                if f.get("cause_id") in ("LOW_INFORMATION_SCENT", "GENERIC_H1")
            ],
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
    responses: Optional[str] = None,
    review: Optional[str] = None,
    skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute end-to-end multi-skill brand AI-readiness audit."""
    inv, specialist_results = collect_telemetry(
        site,
        inventory=inventory,
        analytics=analytics,
        candidate_backlinks=candidate_backlinks,
        responses=responses,
        skills=skills,
    )

    review_data = None
    if review:
        if isinstance(review, dict):
            review_data = review
        elif isinstance(review, (str, bytes, os.PathLike)) and os.path.exists(review):
            try:
                with open(review, "r", encoding="utf-8") as rf:
                    review_data = json.load(rf)
            except Exception as re:
                sys.stderr.write(f"Warning: Failed to parse review file {review}: {re}\n")

    # Cognitive Synthesis
    report = synthesize_audit_report(site, inv, specialist_results, review=review_data)

    # Validate against Draft-07 schema
    schema = load_schema()
    if schema and validate_type is not None:
        err = validate_type(report, schema)
        if err:
            sys.stderr.write(f"Schema Validation Error during audit synthesis: {err}\n")
            raise ValueError(f"Audit report failed Draft-07 schema validation: {err}")

    return report


def sanitize_clean_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Strip auxiliary internal pipeline debug data, leaving only high-signal evaluator fields."""
    clean = {
        "$schema": report.get("$schema", "http://json-schema.org/draft-07/schema#"),
        "schema_version": report.get("schema_version", "1.0.0"),
        "site": report.get("site"),
        "audited_at": report.get("audited_at"),
        "audit_status": report.get("audit_status", "complete"),
        "archetype": report.get("archetype"),
        "summary": report.get("summary"),
        "readiness": report.get("readiness"),
        "findings": [],
        "proactive_actions": [],
    }
    for idx, f in enumerate(report.get("findings", []), start=1):
        clean_f = {
            "id": f.get("id") or f"F-{idx:03d}",
            "cause_id": f.get("cause_id"),
            "title": f.get("title"),
            "severity": f.get("severity"),
            "category": f.get("category"),
            "root_cause": f.get("root_cause"),
            "confidence": f.get("confidence", "high"),
            "scope": f.get("scope"),
            "evidence": f.get("evidence"),
            "impact": f.get("impact"),
            "suggested_action": {
                "summary": f.get("suggested_action", {}).get("summary"),
                "priority": f.get("suggested_action", {}).get("priority", f.get("severity")),
                "technical_fix": f.get("suggested_action", {}).get("technical_fix"),
                "creative_fix": f.get("suggested_action", {}).get("creative_fix"),
                "verification": f.get("suggested_action", {}).get("verification"),
            },
        }
        if f.get("affected_urls"):
            clean_f["affected_urls"] = f.get("affected_urls")
        clean["findings"].append(clean_f)

    for idx, p in enumerate(report.get("proactive_actions", []), start=1):
        clean_p = {
            "id": p.get("id") or f"P-{idx:03d}",
            "title": p.get("title"),
            "summary": p.get("summary"),
            "priority": p.get("priority", "medium"),
        }
        for k in ("category", "technical_fix", "creative_fix", "verification"):
            if p.get(k) is not None:
                clean_p[k] = p.get(k)
        clean["proactive_actions"].append(clean_p)
    return clean


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Master Orchestrator for Brand AI-Readiness & Visibility Audit."
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--inventory", help="Path to pre-crawled site inventory JSON (optional)")
    parser.add_argument("--candidate-backlinks", help="Path to candidate backlinks JSON (optional)")
    parser.add_argument("--analytics", help="Path to first-party analytics JSON (optional)")
    parser.add_argument(
        "--responses", "--observations", dest="responses", help="Path to observed AI assistant outputs JSON to cross-check with fact ledger (optional)"
    )
    parser.add_argument("--review", help="Path to agent review JSON containing refined candidate findings and proactive actions (optional)")
    parser.add_argument("--skills", help="Comma-separated list of specialist skills to execute (e.g. discoverability,entity,geo)")
    parser.add_argument("--output", help="Path to write final JSON report (optional, defaults to stdout)")
    parser.add_argument("--format", choices=["json"], default="json", help="Output format (default: json)")
    parser.add_argument("--telemetry", action="store_true", help="Output raw aggregated sensor telemetry for AI cognitive orchestration")
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Emit automated baseline report directly (reserved for CI/headless verification). AI agents should use --telemetry for cognitive synthesis.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Emit clean, high-signal report containing only core evaluator fields (strips auxiliary manifests and internal DAG meta-tags)",
    )

    args = parser.parse_args()
    skills_list = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else None

    try:
        if args.telemetry:
            payload = get_telemetry_payload(
                site=args.site,
                inventory=args.inventory,
                analytics=args.analytics,
                candidate_backlinks=args.candidate_backlinks,
                responses=args.responses,
                skills=skills_list,
            )
            formatted_output = json.dumps(payload, indent=2)
        else:
            if not args.baseline_only and not args.review:
                sys.stderr.write(
                    "Notice: Emitting automated baseline report. For AI Agent cognitive reasoning workflows, "
                    "use '--telemetry' to extract empirical measurements for agent synthesis.\n"
                )
            report = audit(
                site=args.site,
                inventory=args.inventory,
                analytics=args.analytics,
                candidate_backlinks=args.candidate_backlinks,
                responses=args.responses,
                review=args.review,
                skills=skills_list,
            )
            if args.clean:
                report = sanitize_clean_report(report)
            formatted_output = json.dumps(report, indent=2)
    except Exception as e:
        sys.stderr.write(f"Orchestration Error: {e}\n")
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_output)
            f.write("\n")
        out_dir = os.path.dirname(os.path.abspath(args.output))
        if os.path.isdir(out_dir) and not args.telemetry and not args.clean:
            manifest_file = os.path.join(out_dir, "run-manifest.json")
            try:
                with open(manifest_file, "w", encoding="utf-8") as mf:
                    json.dump(report.get("run_manifest", {}), mf, indent=2)
            except Exception:
                pass
        print(f"Audit report written to {args.output}")
    else:
        print(formatted_output)


if __name__ == "__main__":
    main()
