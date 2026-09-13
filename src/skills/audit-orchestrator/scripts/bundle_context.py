#!/usr/bin/env python3
"""
bundle_context.py - Context Bundler CLI for Brand AI-Readiness & Visibility Audit.
Analyzes site inventory, detects archetype & technical signals, and compiles a single
tailored reference briefing from the knowledge base in a single pass without tool friction.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
REFERENCES_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "references"))

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from causal_gate import detect_business_archetype
except ImportError:
    try:
        from orchestrator import detect_business_archetype
    except ImportError:
        detect_business_archetype = None


def detect_signals(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Detects site archetype, internationalization, and content signals from inventory or telemetry."""
    default_signals = {
        "archetype": "corporate",
        "is_multilingual": False,
        "has_pricing": False,
        "has_schema": False,
        "low_depth_pages": 0,
        "has_robots_blocking": False,
        "has_rendering_gap": False,
        "has_schema_omission": False,
        "has_fact_conflicts": False,
        "has_authority_gaps": False,
        "has_citability_deficit": False,
        "has_engagement_friction": False,
    }
    if not data or not isinstance(data, dict):
        return default_signals

    # Determine if data is raw inventory or telemetry payload
    inv = data.get("inventory") if (isinstance(data, dict) and "inventory" in data and isinstance(data.get("inventory"), dict)) else data
    pages = inv.get("pages", []) if isinstance(inv, dict) else []

    signals = dict(default_signals)

    # Telemetry direct signal extraction if available
    if "archetype" in data:
        signals["archetype"] = data["archetype"]
    if "retrieval" in data and isinstance(data["retrieval"], dict):
        ret = data["retrieval"]
        allowed = ret.get("retrieval_bots_allowed")
        total = ret.get("retrieval_bots_total")
        if allowed is not None and total is not None and allowed < total:
            signals["has_robots_blocking"] = True
        if ret.get("noindex_pages"):
            signals["has_robots_blocking"] = True
    if "rendering" in data and isinstance(data["rendering"], dict) and (
        data["rendering"].get("spa_root_markers_detected") or (data["rendering"].get("visible_words_initial_html", 100) or 0) < 50
    ):
        signals["has_rendering_gap"] = True
    if "entity" in data and isinstance(data["entity"], dict):
        ent = data["entity"]
        if not ent.get("jsonld_present") or not ent.get("types_declared"):
            signals["has_schema_omission"] = True
    if "facts" in data and isinstance(data["facts"], dict) and (data["facts"].get("fact_conflicts", 0) or 0) > 0:
        signals["has_fact_conflicts"] = True
    if "corroboration" in data and isinstance(data["corroboration"], dict):
        corr = data["corroboration"]
        if corr.get("sameas_declared", 0) == 0 or len(corr.get("broken_authority_anchors", [])) > 0:
            signals["has_authority_gaps"] = True
    if "geo" in data and isinstance(data["geo"], dict):
        cit_score = data["geo"].get("average_citability_score")
        if cit_score is not None and cit_score < 65.0:
            signals["has_citability_deficit"] = True
    if "engagement" in data and isinstance(data["engagement"], dict):
        eng = data["engagement"]
        if eng.get("generic_h1_pages"):
            signals["has_engagement_friction"] = True

    # Page-level heuristic analysis
    url_corpus = " ".join((p.get("url") or "").lower() for p in pages if isinstance(p, dict))
    text_corpus_parts = []
    for p in pages:
        if isinstance(p, dict):
            if p.get("html"):
                text_corpus_parts.append(str(p["html"])[:2000].lower())
            if p.get("clean_text"):
                text_corpus_parts.append(str(p["clean_text"])[:2000].lower())
            if p.get("clean_markdown"):
                text_corpus_parts.append(str(p["clean_markdown"])[:2000].lower())
            if p.get("title"):
                text_corpus_parts.append(str(p["title"]).lower())
            if p.get("h1"):
                text_corpus_parts.append(str(p["h1"]).lower())
            if p.get("description"):
                text_corpus_parts.append(str(p["description"]).lower())
            if p.get("page_type"):
                text_corpus_parts.append(str(p["page_type"]).lower())
    text_corpus = " ".join(text_corpus_parts)

    # Detect internationalization
    if re.search(r"/(en|es|fr|de|ja|it|pt|zh|ko|nl|sv|ar|ru)(-[a-z]{2})?(/|$|\?|#)", url_corpus):
        signals["is_multilingual"] = True
    if "hreflang" in text_corpus or any(p.get("language") and p.get("language") != "en" for p in pages if isinstance(p, dict)) or any(p.get("hreflangs") for p in pages if isinstance(p, dict)):
        signals["is_multilingual"] = True

    # Detect pricing / commerce
    if any(k in url_corpus for k in ("/product", "/shop", "/cart", "/checkout", "/item", "/pricing", "/plans")) or any(
        (p.get("page_type") in ("product", "product_detail", "pricing", "cart", "checkout"))
        for p in pages if isinstance(p, dict)
    ) or any(k in text_corpus for k in ("add to cart", "buy now", "pricecurrency", "$", "eur", "usd")):
        signals["has_pricing"] = True

    # Business archetype classification
    if signals["archetype"] == "corporate":
        if detect_business_archetype is not None and isinstance(inv, dict):
            signals["archetype"] = detect_business_archetype(inv)
        else:
            ecom_indicators = ["add to cart", "buy now", "sku", "in stock", "shopping bag", "pricecurrency", "product"]
            saas_indicators = ["pricing", "api docs", "sign up free", "per user", "monthly plan", "workspace", "softwareapplication"]
            pub_indicators = ["published by", "news", "editorial team", "min read", "opinion", "article", "newsarticle"]
            local_indicators = ["localbusiness", "postaladdress", "openinghours", "store-locator", "location", "branches"]

            ecom_count = sum(1 for ind in ecom_indicators if ind in text_corpus)
            saas_count = sum(1 for ind in saas_indicators if ind in text_corpus)
            pub_count = sum(1 for ind in pub_indicators if ind in text_corpus)
            local_count = sum(1 for ind in local_indicators if ind in text_corpus)

            scores = [
                (ecom_count, "ecommerce"),
                (saas_count, "saas"),
                (pub_count, "publisher"),
                (local_count, "local_business"),
            ]
            scores.sort(key=lambda x: x[0], reverse=True)
            if scores[0][0] >= 2:
                signals["archetype"] = scores[0][1]

    low_depth_count = 0
    for p in pages:
        if isinstance(p, dict):
            w_cnt = p.get("word_count", 0)
            if isinstance(w_cnt, (int, float)) and w_cnt < 50:
                low_depth_count += 1
            if float(p.get("snr", 1.0) or 1.0) < 0.05:
                signals["has_rendering_gap"] = True
    signals["low_depth_pages"] = low_depth_count
    if low_depth_count > 0:
        signals["has_citability_deficit"] = True

    return signals


def extract_section(file_path: str, heading_prefix: str, max_chars: int = 3000) -> Optional[str]:
    """Extracts a section starting with heading_prefix from a markdown file."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        idx = content.find(heading_prefix)
        if idx == -1:
            return None
        sub = content[idx:]
        next_sec = sub.find("\n## ", len(heading_prefix))
        if next_sec != -1:
            sub = sub[:next_sec].strip()
        return sub[:max_chars]
    except Exception:
        return None


def build_bundle(
    site: str,
    data: Optional[Dict[str, Any]] = None,
    *,
    archetype: Optional[str] = None,
    topic: Optional[str] = None,
) -> str:
    """Builds unified markdown briefing for the AI agent with dynamic archetype and domain rules."""
    signals = detect_signals(data)
    if archetype:
        signals["archetype"] = archetype.lower().strip()
    output_lines: List[str] = []

    # 1. Baseline Core Synthesis Digest
    digest_path = os.path.join(REFERENCES_DIR, "core-synthesis-digest.md")
    if os.path.exists(digest_path):
        with open(digest_path, "r", encoding="utf-8") as f:
            output_lines.append(f.read())
    else:
        output_lines.append("# Core Synthesis Digest: Brand AI-Readiness & GEO Audit\n")

    output_lines.append("\n---\n")
    output_lines.append(f"## Tailored Cognitive Briefing for `{site}`\n")
    output_lines.append(f"- **Detected Archetype**: `{signals['archetype']}`")
    output_lines.append(f"- **Multilingual Localization**: `{signals['is_multilingual']}`")
    output_lines.append(f"- **Commercial / Pricing Features**: `{signals['has_pricing']}`")
    output_lines.append(f"- **Low-Depth Content Pages**: `{signals['low_depth_pages']}`")
    output_lines.append(f"- **AI Retrieval Blocking Observed**: `{signals['has_robots_blocking']}`")
    output_lines.append(f"- **Client-Side Rendering Risk**: `{signals['has_rendering_gap']}`")
    output_lines.append(f"- **Structured Data Deficit**: `{signals['has_schema_omission']}`")
    output_lines.append(f"- **Fact Ledger Contradictions**: `{signals['has_fact_conflicts']}`")
    output_lines.append(f"- **Authority Anchor Gaps**: `{signals['has_authority_gaps']}`")
    output_lines.append(f"- **Citability / Depth Deficit**: `{signals['has_citability_deficit']}`")
    output_lines.append(f"- **Engagement Handoff Friction**: `{signals['has_engagement_friction']}`")
    output_lines.append("\n### Applicable Specialized Rules & Templates:\n")

    # 2. Archetype-Specific Rules & Code Templates
    arch = signals["archetype"]
    if arch == "ecommerce":
        ecom_sec = extract_section(
            os.path.join(SKILLS_DIR, "entity-content-audit", "references", "knowledge-base.md"),
            "## 2. Product & Offer Schema with Full Answerability",
        )
        if ecom_sec:
            output_lines.append("#### E-Commerce Product & Offer Schema Template (Required Commercial Fields):")
            output_lines.append(ecom_sec)
            output_lines.append("\n*(extracted from entity-content-audit knowledge-base.md)*\n")
        intent_sec = extract_section(
            os.path.join(SKILLS_DIR, "engagement-context-audit", "references", "knowledge-base.md"),
            "## 4. Intent-to-Landing Match",
        )
        if intent_sec:
            output_lines.append("#### E-Commerce Intent-to-Landing Handoff Rubric:")
            output_lines.append(intent_sec)
            output_lines.append("\n*(extracted from engagement-context-audit knowledge-base.md)*\n")

    elif arch == "saas":
        pricing_sec = extract_section(
            os.path.join(SKILLS_DIR, "engagement-context-audit", "references", "knowledge-base.md"),
            "## 7. Autonomous AI Buying Agent Readiness (`/pricing.md`)",
        )
        if pricing_sec:
            output_lines.append("#### SaaS Machine-Readable `/pricing.md` Specification:")
            output_lines.append(pricing_sec)
            output_lines.append("\n*(extracted from engagement-context-audit knowledge-base.md)*\n")
        table_sec = extract_section(
            os.path.join(SKILLS_DIR, "geo-content-audit", "references", "knowledge-base.md"),
            "## 2. Semantic Attribute Comparison Table Pattern",
        )
        if table_sec:
            output_lines.append("#### SaaS Feature Comparison Table Pattern (Princeton KDD 2024):")
            output_lines.append(table_sec)
            output_lines.append("\n*(extracted from geo-content-audit knowledge-base.md)*\n")

    elif arch == "publisher":
        graph_sec = extract_section(
            os.path.join(SKILLS_DIR, "entity-content-audit", "references", "knowledge-base.md"),
            "## 1. Master Linked Graph Template",
        )
        if graph_sec:
            output_lines.append("#### Publisher Master Linked Graph Template (Organization + Person Authorship):")
            output_lines.append(graph_sec)
            output_lines.append("\n*(extracted from entity-content-audit knowledge-base.md)*\n")
        qa_sec = extract_section(
            os.path.join(SKILLS_DIR, "geo-content-audit", "references", "knowledge-base.md"),
            "## 1. Direct Q&A Answer-Block Pattern (AutoGEO)",
        )
        if qa_sec:
            output_lines.append("#### Publisher Direct Q&A Answer-Block Pattern (+40.9% Citation Lift):")
            output_lines.append(qa_sec)
            output_lines.append("\n*(extracted from geo-content-audit knowledge-base.md)*\n")

    elif arch == "local_business":
        loc_sec = extract_section(
            os.path.join(SKILLS_DIR, "entity-content-audit", "references", "knowledge-base.md"),
            "## 3. LocalBusiness Schema Template",
        )
        if loc_sec:
            output_lines.append("#### LocalBusiness Schema Template (GeoCoordinates, PostalAddress, OpeningHours):")
            output_lines.append(loc_sec)
            output_lines.append("\n*(extracted from entity-content-audit knowledge-base.md)*\n")

    else:
        graph_sec = extract_section(
            os.path.join(SKILLS_DIR, "entity-content-audit", "references", "knowledge-base.md"),
            "## 1. Master Linked Graph Template",
        )
        if graph_sec:
            output_lines.append("#### Master Linked Graph Template (Organization + WebSite):")
            output_lines.append(graph_sec)
            output_lines.append("\n*(extracted from entity-content-audit knowledge-base.md)*\n")

    # 3. Triggered Specialized Checklists
    if signals["is_multilingual"]:
        intl_content = extract_section(
            os.path.join(SKILLS_DIR, "discoverability-audit", "references", "knowledge-base.md"),
            "## 7. International SEO",
        )
        if intl_content:
            output_lines.append("#### International SEO & Localization Checklist:")
            output_lines.append(intl_content)
            output_lines.append("\n*(extracted from discoverability-audit knowledge-base.md)*\n")

    if signals["has_robots_blocking"]:
        robots_sec = extract_section(
            os.path.join(SKILLS_DIR, "discoverability-audit", "references", "knowledge-base.md"),
            "## 1. robots.txt & Access Directives (RFC 9309)",
        )
        if robots_sec:
            output_lines.append("#### RFC 9309 Crawler Matrix & Retrieval Permission Rules:")
            output_lines.append(robots_sec)
            output_lines.append("\n*(extracted from discoverability-audit knowledge-base.md)*\n")

    if signals["has_rendering_gap"]:
        render_sec = extract_section(
            os.path.join(SKILLS_DIR, "discoverability-audit", "references", "knowledge-base.md"),
            "## 4. Rendering & Content Extractability",
        )
        if render_sec:
            output_lines.append("#### Client-Side Rendering Shell Extraction Thresholds:")
            output_lines.append(render_sec)
            output_lines.append("\n*(extracted from discoverability-audit knowledge-base.md)*\n")

    if signals["has_fact_conflicts"]:
        fact_sec = extract_section(
            os.path.join(SKILLS_DIR, "fact-consistency-audit", "references", "knowledge-base.md"),
            "## 1. Contextual Scope Invariant & False-Positive Prevention",
        )
        if fact_sec:
            output_lines.append("#### First-Party Fact Ledger & Contradiction Resolution Guidelines:")
            output_lines.append(fact_sec)
            output_lines.append("\n*(extracted from fact-consistency-audit knowledge-base.md)*\n")

    if signals["has_authority_gaps"]:
        auth_sec = extract_section(
            os.path.join(SKILLS_DIR, "corroboration-authority-audit", "references", "knowledge-base.md"),
            "## 2. Declared Identity Nodes vs. Verified Candidate Backlinks",
        )
        if auth_sec:
            output_lines.append("#### Tier-1 Authority Anchors & sameAs Identity Substantiation Protocol:")
            output_lines.append(auth_sec)
            output_lines.append("\n*(extracted from corroboration-authority-audit knowledge-base.md)*\n")

    if signals["has_citability_deficit"] or signals["low_depth_pages"] > 0:
        conjunction_sec = extract_section(
            os.path.join(SKILLS_DIR, "geo-content-audit", "references", "knowledge-base.md"),
            "## 3. Princeton KDD 2024 Causal Conjunction Cheatsheet",
        )
        if conjunction_sec:
            output_lines.append("#### Princeton KDD 2024 Causal Conjunction Cheatsheet (+28.2% Lift):")
            output_lines.append(conjunction_sec)
            output_lines.append("\n*(extracted from geo-content-audit knowledge-base.md)*\n")

        fluff_sec = extract_section(
            os.path.join(SKILLS_DIR, "geo-content-audit", "references", "knowledge-base.md"),
            "## 9. AI Writing Detection & Natural Content Patterns",
        )
        if fluff_sec:
            output_lines.append("#### AI Writing Detection & Promotional Fluff Elimination Guardrails:")
            output_lines.append(fluff_sec)
            output_lines.append("\n*(extracted from geo-content-audit knowledge-base.md)*\n")

    if signals["has_engagement_friction"]:
        orient_sec = extract_section(
            os.path.join(SKILLS_DIR, "engagement-context-audit", "references", "knowledge-base.md"),
            "## 1. The 4-Question First-Visit Orientation Test",
        )
        if orient_sec:
            output_lines.append("#### 5-Second First-Visit Orientation Framework:")
            output_lines.append(orient_sec)
            output_lines.append("\n*(extracted from engagement-context-audit knowledge-base.md)*\n")

    # 4. Optional Focused Topic Extraction
    if topic:
        topic_lower = topic.lower().strip()
        topic_map = {
            "retrieval": ("discoverability-audit", "## 1. robots.txt & Access Directives (RFC 9309)"),
            "discoverability": ("discoverability-audit", "## 1. robots.txt & Access Directives (RFC 9309)"),
            "rendering": ("discoverability-audit", "## 4. Rendering & Content Extractability"),
            "entity": ("entity-content-audit", "## 1. Master Linked Graph Template"),
            "schema": ("entity-content-audit", "## 1. Master Linked Graph Template"),
            "facts": ("fact-consistency-audit", "## 1. Contextual Scope Invariant & False-Positive Prevention"),
            "corroboration": ("corroboration-authority-audit", "## 2. Declared Identity Nodes vs. Verified Candidate Backlinks"),
            "authority": ("corroboration-authority-audit", "## 2. Declared Identity Nodes vs. Verified Candidate Backlinks"),
            "geo": ("geo-content-audit", "## 3. Princeton KDD 2024 Causal Conjunction Cheatsheet"),
            "citability": ("geo-content-audit", "## 1. Direct Q&A Answer-Block Pattern (AutoGEO)"),
            "engagement": ("engagement-context-audit", "## 1. The 4-Question First-Visit Orientation Test"),
            "orientation": ("engagement-context-audit", "## 1. The 4-Question First-Visit Orientation Test"),
        }
        if topic_lower in topic_map:
            skill_folder, sec_heading = topic_map[topic_lower]
            extracted = extract_section(
                os.path.join(SKILLS_DIR, skill_folder, "references", "knowledge-base.md"),
                sec_heading,
                max_chars=3500,
            )
            if extracted:
                output_lines.append(f"\n### Topic Deep-Dive: `{topic}`\n")
                output_lines.append(extracted)
                output_lines.append(f"\n*(extracted from {skill_folder} references/knowledge-base.md)*\n")

    return "\n".join(output_lines)


def verify_reference_integrity() -> Dict[str, Any]:
    """Verify presence and calculate SHA-256 checksums of core knowledge base and schema references."""
    ref_files = [
        "checks.json",
        "knowledge-base.md",
        "core-synthesis-digest.md",
        "report-schema.json",
        "telemetry-schema.json",
    ]
    status: Dict[str, Any] = {"all_valid": True, "references": {}}
    for fname in ref_files:
        fpath = os.path.join(REFERENCES_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                chash = hashlib.sha256(f.read()).hexdigest()
            status["references"][fname] = {
                "present": True,
                "sha256": chash,
                "size_bytes": os.path.getsize(fpath),
            }
        else:
            status["all_valid"] = False
            status["references"][fname] = {
                "present": False,
                "sha256": None,
                "size_bytes": 0,
            }
    return status


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Bundle and compile relevant knowledge base context for a given target site."
    )
    parser.add_argument("--site", default="https://example.com", help="Target site URL or domain")
    parser.add_argument("--inventory", help="Path to pre-crawled inv.json site inventory (optional)")
    parser.add_argument("--telemetry", help="Path to telemetry.json payload (optional)")
    parser.add_argument("--archetype", choices=["ecommerce", "saas", "publisher", "local_business", "corporate"], help="Explicitly force business archetype context")
    parser.add_argument("--topic", help="Scope context bundle to specific technical topic (e.g. retrieval, rendering, entity, facts, corroboration, geo, engagement)")
    parser.add_argument("--output", help="Path to write compiled briefing (optional, defaults to stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")

    args = parser.parse_args()

    data_payload: Optional[Dict[str, Any]] = None
    source_file = args.telemetry or args.inventory
    if source_file and os.path.exists(source_file):
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                data_payload = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load context source from {source_file}: {e}\n")

    bundle_text = build_bundle(args.site, data_payload, archetype=args.archetype, topic=args.topic)

    if args.format == "json":
        signals = detect_signals(data_payload)
        ref_status = verify_reference_integrity()
        out = json.dumps({
            "site": args.site,
            "signals": signals,
            "reference_integrity": ref_status,
            "briefing": bundle_text,
        }, indent=2)
    else:
        out = bundle_text

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
            f.write("\n")
        print(f"Context bundle written to {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()
