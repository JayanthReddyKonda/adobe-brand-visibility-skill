#!/usr/bin/env python3
"""run_scraper.py - Production CLI entrypoint for the web-scraper skill.

Autonomous, zero-dependency, SSRF-hardened web crawler and AI-content extractor.
Crawls public websites, parses RFC 9309 robots.txt permissions across 16 AI retrieval & training bots,
traverses XML sitemaps, extracts Trafilatura-grade clean Markdown, flattens Schema.org JSON-LD graphs,
scores commercial routes, and emits structured site inventories for downstream AI agents.

Usage:
    python3 skills/web-scraper/scripts/run_scraper.py --site https://example.com --output inv.json --format json
    python3 skills/web-scraper/scripts/run_scraper.py --site https://example.com --max-pages 10 --timeout 20
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from crawler.engine import WebAuditEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous AI-Optimized Web Crawler & Content Extractor (Zero Third-Party Dependencies)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--site",
        "-s",
        required=True,
        help="Target website URL or domain (e.g., https://example.com)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="Path to write output inventory JSON (if omitted, printed to stdout)",
    )
    parser.add_argument(
        "--max-pages",
        "-p",
        type=int,
        default=15,
        help="Maximum pages to crawl within origin",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=30.0,
        help="Monotonic crawl deadline timeout in seconds",
    )
    parser.add_argument(
        "--max-depth",
        "-d",
        type=int,
        default=3,
        help="Maximum link traversal depth from homepage",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "both"],
        default="json",
        help="Output serialization format",
    )
    parser.add_argument(
        "--strict-robots",
        action="store_true",
        help="Abort crawling if robots.txt disallows entrypoint",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Emit diagnostic crawl progress to stderr",
    )
    return parser.parse_args()


def format_markdown_summary(inventory: dict) -> str:
    """Generate human-readable Markdown summary of acquired inventory."""
    site = inventory.get("site", "Unknown")
    pages = inventory.get("pages", [])
    robots = inventory.get("robots", {})
    sitemaps = inventory.get("sitemaps", [])
    stats = inventory.get("stats", {})
    infra = inventory.get("infrastructure", {})

    total_ctas = sum(len(p.get("ctas", [])) for p in pages)
    total_social = sum(len(p.get("social_links", [])) for p in pages)

    md = [
        f"# Web Scraping Inventory: {site}",
        "",
        f"- **Crawled At:** {inventory.get('crawled_at', 'N/A')}",
        f"- **Pages Acquired:** {len(pages)}",
        f"- **Sitemaps Discovered:** {len(sitemaps)}",
        f"- **Total CTAs Extracted:** {total_ctas}",
        f"- **Social / Contact Anchors Found:** {total_social}",
        f"- **Total Bytes:** {stats.get('total_bytes', 0):,} bytes",
        f"- **Duration:** {stats.get('elapsed_seconds', 0.0):.2f}s",
        "",
        "## AI Discovery & Infrastructure Manifests",
        "",
        "| Manifest | Status | Path |",
        "|---|---|---|",
    ]

    manifests = [
        ("llms.txt", infra.get("llms_txt", {})),
        ("pricing.md", infra.get("pricing_md", {})),
        ("ai-plugin.json", infra.get("ai_plugin", {})),
        ("security.txt", infra.get("security_txt", {})),
    ]
    for name, item in manifests:
        pres = item.get("present", False)
        status = "Present" if pres else "Not Discovered"
        path = f"`{item.get('path', '')}`" if pres and item.get("path") else "-"
        md.append(f"| `{name}` | {status} | {path} |")

    md.extend([
        "",
        "## AI Crawler Bot Access Matrix",
        "",
        "| Crawler Bot | Permitted | Role |",
        "|---|---|---|",
    ])

    matrix = robots.get("matrix", {})
    for bot, allowed in sorted(matrix.items()):
        status = "Allowed" if allowed else "Blocked"
        role = "Search Retrieval" if any(x in bot.lower() for x in ["search", "perplexity", "bing"]) else "Foundation Training"
        md.append(f"| `{bot}` | {status} | {role} |")

    md.extend([
        "",
        "## Acquired Pages Inventory",
        "",
        "| URL | Type | Status | SNR | Words | JSON-LD Entities | CTAs |",
        "|---|---|---|---|---|---|---|",
    ])

    for p in pages:
        u = p.get("url", "")
        ptype = p.get("page_type", "unknown")
        code = p.get("status", 0)
        snr = f"{p.get('snr', 0.0):.2f}"
        words = p.get("word_count", 0)
        entities = len(p.get("jsonld", []))
        ctas = len(p.get("ctas", []))
        md.append(f"| `{u}` | `{ptype}` | {code} | {snr} | {words:,} | {entities} | {ctas} |")

    return "\n".join(md)


def main() -> int:
    args = parse_args()
    start_time = time.monotonic()

    if args.verbose:
        sys.stderr.write(f"[*] Starting web-scraper on {args.site} (max_pages={args.max_pages}, timeout={args.timeout}s)...\n")

    engine = WebAuditEngine(
        time_limit_sec=args.timeout,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        strict_robots=args.strict_robots,
    )

    crawl_error = None
    try:
        engine.crawl(args.site)
    except Exception as exc:
        sys.stderr.write(f"[!] Crawl encountered error: {exc}\n")
        crawl_error = str(exc)

    elapsed = time.monotonic() - start_time
    inventory = engine.to_inventory_dict()
    if "stats" not in inventory or not isinstance(inventory["stats"], dict):
        inventory["stats"] = {}
    inventory["stats"]["elapsed_seconds"] = elapsed
    if crawl_error:
        inventory["error"] = crawl_error
        inventory["status"] = "failed"

    if args.verbose:
        sys.stderr.write(
            f"[*] Scraping complete: {len(inventory.get('pages', []))} pages acquired in {elapsed:.2f}s.\n"
        )

    json_str = json.dumps(inventory, indent=2)
    md_str = format_markdown_summary(inventory) if args.format in ("markdown", "both") else ""

    if args.output:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        content_to_write = md_str if args.format == "markdown" else json_str
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content_to_write)
        if args.verbose:
            sys.stderr.write(f"[*] Inventory written to {args.output}\n")

    if args.format == "json":
        if not args.output:
            print(json_str)
    elif args.format == "markdown":
        print(md_str)
    elif args.format == "both":
        if not args.output:
            print(json_str)
        print("\n---\n")
        print(md_str)

    if crawl_error and len(inventory.get("pages", [])) == 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
