#!/usr/bin/env python3
"""acquire_inventory.py - Type-safe, SSRF-bounded inventory acquisition utility.

Crawls the target homepage, robots.txt, and XML sitemaps, extracting and filtering
genuine HTML pages for downstream specialist audits while isolating infrastructure resources.
Delegates to WebAuditEngine for high-performance single-pass acquisition.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from crawler.engine import EvidenceExtractor, PageClassifier, WebAuditEngine  # type: ignore

NON_HTML_EXTENSIONS = (
    ".xml",
    ".xml.gz",
    ".txt",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".mp4",
    ".mp3",
    ".json",
    ".js",
    ".css",
    ".zip",
    ".gz",
    ".tar",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
)


def normalize_target(site: str) -> Tuple[str, str]:
    s = site.strip()
    if not s.startswith(("http://", "https://")):
        base = f"https://{s.split('/')[0]}"
    else:
        parts = s.split("://", 1)
        base = f"{parts[0]}://{parts[1].split('/')[0]}"
    return urlparse(base).netloc, base


def classify_page(url: str, title: str = "") -> Tuple[str, float, str, str]:
    """Compatibility shim delegating to PageClassifier."""
    res = PageClassifier.classify(url=url, title=title)
    return res["value"], res["confidence"], res.get("template", "general"), res.get("locale", "en")


def extract_clean_content(html: str) -> Dict[str, Any]:
    """Compatibility shim delegating to EvidenceExtractor."""
    clean_text = EvidenceExtractor.strip_boilerplate(html)
    word_count = len(clean_text.split())
    snr = EvidenceExtractor.calculate_text_density_ratio(clean_text, html)
    return {
        "clean_text": clean_text,
        "clean_word_count": word_count,
        "snr": snr,
        "has_main": "<main" in html.lower(),
        "has_article": "<article" in html.lower(),
        "has_header": "<header" in html.lower(),
        "has_nav": "<nav" in html.lower(),
        "has_footer": "<footer" in html.lower(),
    }


def build_inventory(
    site: str,
    max_pages: int = 28,
    timeout_seconds: float = 90,
    deadline: Optional[float] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Crawls target domain and constructs canonical site inventory dictionary."""
    start_mono = time.monotonic()
    if deadline is None:
        deadline = start_mono + timeout_seconds
    domain, base_url = normalize_target(site)

    effective_timeout = max(5.0, (deadline - time.monotonic()) if deadline else timeout_seconds)
    engine = WebAuditEngine(time_limit_sec=effective_timeout, max_pages=max_pages)
    crawl_error = None
    try:
        engine.crawl(base_url)
    except Exception as e:
        crawl_error = {"type": type(e).__name__, "message": str(e)}

    inv_dict = engine.to_inventory_dict()
    inv_dict["site"] = domain
    inv_dict["base_url"] = base_url
    inv_dict.setdefault("limitations", [])
    if crawl_error:
        inv_dict["crawl_error"] = crawl_error
        inv_dict["limitations"].append(f"Crawl aborted with {crawl_error['type']}: {crawl_error['message']}")
    if not engine.pages:
        inv_dict["limitations"].append("Homepage unreachable or non-HTML; inventory could not be built.")
        inv_dict["status"] = "failed"
    elif crawl_error:
        inv_dict["status"] = "partial"
    else:
        inv_dict["status"] = "complete"

    elapsed = round(time.monotonic() - start_mono, 1)
    inv_dict["elapsed_seconds"] = elapsed

    stats = {
        "homepage_reachable": inv_dict["infrastructure"]["homepage_reachable"],
        "html_pages_sampled": len(inv_dict["pages"]),
        "sitemaps_found": len(inv_dict["infrastructure"]["sitemaps_discovered"]),
        "sitemaps_processed": inv_dict["infrastructure"]["sitemaps_processed"],
        "urls_discovered": inv_dict["infrastructure"]["urls_extracted"],
        "same_origin_urls": inv_dict["infrastructure"]["same_origin_urls"],
        "elapsed_seconds": elapsed,
        "page_types": {
            t: sum(1 for p in inv_dict["pages"] if p.get("page_type") == t)
            for t in {p.get("page_type") for p in inv_dict["pages"] if p.get("page_type")}
        },
    }
    return inv_dict, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Single-Pass Site Inventory Acquisition Utility.\n"
            "Crawls target homepage, robots.txt, XML sitemaps, and content routes under strict socket-level "
            "zero-trust SSRF sandboxing (safe_fetch.py). Emits canonical inv.json consumed offline by all "
            "downstream specialist diagnostic sensors, ensuring single-pass efficiency."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("site_pos", nargs="?", default=None, metavar="SITE", help="Target website URL or domain")
    parser.add_argument("--site", "-s", default=None, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--output", "-o", help="Destination path to write acquired inventory JSON (e.g. inv.json)")
    parser.add_argument("--max-pages", "-m", "-p", type=int, default=15, help="Maximum pages to acquire (default: 15)")
    parser.add_argument("--timeout", "-t", type=float, default=45.0, help="Acquisition timeout in seconds (default: 45.0)")
    parser.add_argument("--concurrency", "-c", type=int, default=1, help="Max concurrent acquisition workers (default: 1)")
    parser.add_argument("--format", choices=["json"], default="json", help="Output serialization format (default: json)")
    args = parser.parse_args()

    raw_site = args.site or args.site_pos
    if not raw_site:
        parser.error("Target website URL is required (provide positionally or via --site / -s)")

    s = raw_site.strip()
    if not s.startswith(("http://", "https://")):
        base_url = f"https://{s.split('/')[0]}"
    else:
        parts = s.split("://", 1)
        base_url = f"{parts[0]}://{parts[1].split('/')[0]}"

    inv, stats = build_inventory(base_url, max_pages=args.max_pages, timeout_seconds=args.timeout)
    out_data = inv if inv else {"status": "failed", "homepage_reachable": False, "error": stats.get("error")}
    out_json = json.dumps(out_data, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json + "\n")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
