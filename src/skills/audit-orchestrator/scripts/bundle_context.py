#!/usr/bin/env python3
"""
bundle_context.py - Context Bundler CLI for Brand AI-Readiness & Visibility Audit.
Analyzes site inventory, detects archetype & technical signals, and compiles a single
tailored reference briefing from the knowledge base in a single pass without tool friction.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
REFERENCES_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "references"))


def detect_signals(inv: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Detects site archetype, internationalization, and content signals from inventory."""
    if not inv or not isinstance(inv, dict):
        return {
            "archetype": "corporate",
            "is_multilingual": False,
            "has_pricing": False,
            "has_schema": False,
            "low_depth_pages": 0,
        }

    pages = inv.get("pages", [])
    signals = {
        "archetype": "corporate",
        "is_multilingual": False,
        "has_pricing": False,
        "has_schema": False,
        "low_depth_pages": 0,
    }

    url_corpus = " ".join((p.get("url") or "").lower() for p in pages)
    html_corpus = " ".join((p.get("html") or "").lower()[:2000] for p in pages)

    # Detect internationalization
    if any(code in url_corpus for code in ("/es/", "/fr/", "/de/", "/ja/", "/it/", "/pt/", "/zh/")):
        signals["is_multilingual"] = True
    if "hreflang" in html_corpus:
        signals["is_multilingual"] = True

    # Detect pricing / commerce
    if any(k in url_corpus for k in ("/product", "/shop", "/cart", "/checkout", "/item", "/pricing", "/plans")):
        signals["has_pricing"] = True

    # Detect business archetype
    ecom_indicators = ["add to cart", "buy now", "sku", "in stock", "shopping bag", "priceCurrency"]
    saas_indicators = ["pricing", "api docs", "sign up free", "per user", "monthly plan", "workspace"]
    pub_indicators = ["published by", "news", "editorial team", "min read", "opinion", "article"]

    ecom_count = sum(1 for ind in ecom_indicators if ind in html_corpus)
    saas_count = sum(1 for ind in saas_indicators if ind in html_corpus)
    pub_count = sum(1 for ind in pub_indicators if ind in html_corpus)

    if ecom_count >= 2:
        signals["archetype"] = "ecommerce"
    elif saas_count >= 2:
        signals["archetype"] = "saas"
    elif pub_count >= 2:
        signals["archetype"] = "publisher"

    low_depth_count = 0
    for p in pages:
        w_cnt = p.get("word_count", 0)
        if isinstance(w_cnt, (int, float)) and w_cnt < 50:
            low_depth_count += 1
    signals["low_depth_pages"] = low_depth_count

    return signals


def build_bundle(site: str, inv: Optional[Dict[str, Any]] = None) -> str:
    """Builds unified markdown briefing for the AI agent."""
    signals = detect_signals(inv)
    output_lines: List[str] = []

    # 1. Baseline Core Synthesis Digest
    digest_path = os.path.join(REFERENCES_DIR, "core-synthesis-digest.md")
    if os.path.exists(digest_path):
        with open(digest_path, "r", encoding="utf-8") as f:
            output_lines.append(f.read())
    else:
        output_lines.append("# Core Synthesis Digest: Brand AI-Readiness & GEO Audit\n")

    output_lines.append("\n---\n")
    output_lines.append(f"## Tailored Site Context Briefing for `{site}`\n")
    output_lines.append(f"- **Detected Archetype**: `{signals['archetype']}`")
    output_lines.append(f"- **Multilingual Localization Detected**: `{signals['is_multilingual']}`")
    output_lines.append(f"- **Commercial / Pricing Features**: `{signals['has_pricing']}`")
    output_lines.append(f"- **Low-Depth Content Pages**: `{signals['low_depth_pages']}`")
    output_lines.append("\n### Applicable Specialized Rules:\n")

    # 2. Append triggered specialist rules
    if signals["is_multilingual"]:
        intl_path = os.path.join(SKILLS_DIR, "discoverability-audit", "references", "international-seo.md")
        if os.path.exists(intl_path):
            output_lines.append("#### International SEO & Localization Checklist:")
            with open(intl_path, "r", encoding="utf-8") as f:
                output_lines.append(f.read()[:2000])
                output_lines.append("\n*(truncated for brevity)*\n")

    if signals["archetype"] == "ecommerce":
        prod_schema = os.path.join(SKILLS_DIR, "entity-content-audit", "references", "product.json")
        if os.path.exists(prod_schema):
            output_lines.append("#### E-Commerce Schema.org Product Template (Required Fields):")
            with open(prod_schema, "r", encoding="utf-8") as f:
                output_lines.append(f"```json\n{f.read()}\n```\n")

    if signals["low_depth_pages"] > 0:
        ai_detect = os.path.join(SKILLS_DIR, "geo-content-audit", "references", "ai-writing-detection.md")
        if os.path.exists(ai_detect):
            output_lines.append("#### Content Quality & AI Writing Pattern Guardrails:")
            with open(ai_detect, "r", encoding="utf-8") as f:
                output_lines.append(f.read()[:2000])
                output_lines.append("\n*(truncated for brevity)*\n")

    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Bundle and compile relevant knowledge base context for a given target site."
    )
    parser.add_argument("--site", default="https://example.com", help="Target site URL or domain")
    parser.add_argument("--inventory", help="Path to pre-crawled inv.json site inventory (optional)")
    parser.add_argument("--output", help="Path to write compiled briefing (optional, defaults to stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")

    args = parser.parse_args()

    inv: Optional[Dict[str, Any]] = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load inventory from {args.inventory}: {e}\n")

    bundle_text = build_bundle(args.site, inv)

    if args.format == "json":
        signals = detect_signals(inv)
        out = json.dumps({"site": args.site, "signals": signals, "briefing": bundle_text}, indent=2)
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
