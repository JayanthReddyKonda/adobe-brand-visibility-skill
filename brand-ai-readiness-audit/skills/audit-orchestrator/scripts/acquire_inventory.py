#!/usr/bin/env python3
"""
acquire_inventory.py - Type-safe, SSRF-bounded inventory acquisition utility.
Crawls the target homepage, robots.txt, and XML sitemaps, extracting and filtering
genuine HTML pages for downstream specialist audits while isolating infrastructure resources.
"""

import sys
import os
import re
import json
import time
import argparse
from datetime import datetime, timezone
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from safe_fetch import safe_fetch, DEFAULT_USER_AGENT

NON_HTML_EXTENSIONS = (
    ".xml", ".xml.gz", ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif",
    ".svg", ".webp", ".mp4", ".mp3", ".json", ".js", ".css", ".zip",
    ".gz", ".tar", ".ico", ".woff", ".woff2", ".ttf", ".eot"
)

PRIORITY_KEYWORDS = [
    ("product", ["/product/", "/products/", "/p/", "/item/", "/store/", "/shop/"]),
    ("pricing", ["/pricing", "/prices", "/plans", "/billing", "/subscription"]),
    ("service", ["/service", "/services", "/solution", "/solutions", "/offering"]),
    ("category", ["/category/", "/categories/", "/collection/", "/collections/", "/browse/"]),
    ("contact", ["/contact", "/support", "/help", "/reach-us"]),
    ("location", ["/location", "/locations", "/store-locator", "/where-to-buy"]),
    ("about", ["/about", "/company", "/our-team", "/story", "/mission"]),
    ("documentation", ["/docs", "/documentation", "/guide", "/api", "/developer"]),
    ("article", ["/blog/", "/news/", "/article/", "/posts/", "/insights/"]),
]


def is_html_response(headers, body_snippet=""):
    ctype = ""
    for k, v in (headers or {}).items():
        if k.lower() == "content-type":
            ctype = str(v).lower()
            break
    if "text/html" in ctype or "application/xhtml+xml" in ctype:
        return True
    if any(x in ctype for x in ("application/xml", "text/xml", "application/json", "application/pdf", "image/")):
        return False
    snippet = body_snippet.strip()[:200].lower()
    if snippet.startswith("<?xml") or "<urlset" in snippet or "<sitemapindex" in snippet:
        return False
    if "<!doctype html" in snippet or "<html" in snippet:
        return True
    return False


def is_sitemap_or_non_html_url(url):
    u_lower = url.lower().split("?")[0].split("#")[0]
    if u_lower.endswith(NON_HTML_EXTENSIONS):
        return True
    if "sitemap" in u_lower or "feed.xml" in u_lower or "rss.xml" in u_lower or "robots.txt" in u_lower:
        return True
    return False


def classify_page(url, title=""):
    hay = (url + " " + (title or "")).lower()
    for ptype, kws in PRIORITY_KEYWORDS:
        if any(k in hay for k in kws):
            return ptype
    return "other"


def _visible_words(html):
    text = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", html or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(text.split())


def _extract_title(html):
    m = re.search(r"<title[^>]*>([^<]{1,300})</title>", html or "", re.I)
    return m.group(1).strip() if m else ""


def _parse_sitemap_xml(sitemap_body):
    child_sitemaps = []
    page_urls = []
    if not sitemap_body or "<loc>" not in sitemap_body:
        return child_sitemaps, page_urls
    locs = [loc.strip() for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap_body, re.IGNORECASE)]
    if "<sitemapindex" in sitemap_body.lower():
        child_sitemaps = locs
    else:
        page_urls = locs
    return child_sitemaps, page_urls


def build_inventory(base_url, max_pages=16, deadline=None):
    start = time.time()
    parsed_base = urlparse(base_url)
    target_netloc = parsed_base.netloc.lower()

    inv = {
        "base_url": base_url,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "infrastructure": {
            "robots": None,
            "sitemaps_discovered": [],
            "sitemaps_processed": 0,
            "urls_extracted": 0,
            "same_origin_urls": 0
        },
        "robots": None,
        "pages": [],
        "limitations": []
    }

    # 1. Homepage
    status, home_html, home_headers, err = safe_fetch(base_url + "/", timeout=10, max_bytes=2*1024*1024)
    if not home_html or status is None:
        return None, {"homepage_reachable": False, "error": err}

    if is_html_response(home_headers, home_html):
        inv["pages"].append({
            "url": base_url + "/",
            "status": status,
            "resource_type": "html",
            "content_type": home_headers.get("content-type", "text/html"),
            "page_type": "homepage",
            "title": _extract_title(home_html),
            "word_count": _visible_words(home_html),
            "html": home_html
        })

    if deadline and time.time() >= deadline:
        inv["limitations"].append("Inventory truncated at acquisition deadline.")
        return inv, {
            "homepage_reachable": True,
            "html_pages_sampled": len(inv["pages"]),
            "sitemaps_processed": 0,
            "elapsed_seconds": round(time.time() - start, 1)
        }

    # 2. robots.txt
    r_status, robots_txt, _, _ = safe_fetch(base_url + "/robots.txt", timeout=8, max_bytes=512*1024)
    inv["robots"] = {"status": r_status, "text": robots_txt if r_status == 200 else None}
    inv["infrastructure"]["robots"] = inv["robots"]

    sitemap_candidates = []
    if robots_txt and r_status == 200:
        sitemap_candidates = [l.split(":", 1)[1].strip() for l in robots_txt.splitlines()
                              if l.lower().startswith("sitemap:")][:5]
    if not sitemap_candidates:
        sitemap_candidates = [base_url + "/sitemap.xml"]

    # 3. Sitemaps
    extracted_page_urls = []
    sitemaps_to_process = list(sitemap_candidates)
    processed_sitemaps = set()

    while sitemaps_to_process and len(processed_sitemaps) < 8:
        if deadline and time.time() >= deadline:
            break
        sm_url = sitemaps_to_process.pop(0)
        if sm_url in processed_sitemaps:
            continue
        sm_netloc = urlparse(sm_url).netloc.lower()
        if sm_netloc and sm_netloc != target_netloc:
            continue

        processed_sitemaps.add(sm_url)
        inv["infrastructure"]["sitemaps_discovered"].append(sm_url)

        s_status, s_body, _, _ = safe_fetch(sm_url, timeout=8, max_bytes=2*1024*1024)
        if s_status == 200 and s_body:
            inv["infrastructure"]["sitemaps_processed"] += 1
            child_sms, raw_page_urls = _parse_sitemap_xml(s_body)
            for c_sm in child_sms:
                if c_sm not in processed_sitemaps and urlparse(c_sm).netloc.lower() == target_netloc:
                    sitemaps_to_process.append(c_sm)
            for pu in raw_page_urls:
                if urlparse(pu).netloc.lower() == target_netloc and not is_sitemap_or_non_html_url(pu):
                    extracted_page_urls.append(pu)

    inv["infrastructure"]["urls_extracted"] = len(extracted_page_urls)
    unique_page_urls = list(dict.fromkeys(extracted_page_urls))
    inv["infrastructure"]["same_origin_urls"] = len(unique_page_urls)

    # 4. Selection of Representative HTML Pages
    seen_urls = {p["url"].rstrip("/") for p in inv["pages"]}
    by_type = {}
    for u in unique_page_urls:
        u_clean = u.rstrip("/")
        if u_clean in seen_urls or u_clean == base_url.rstrip("/"):
            continue
        ptype = classify_page(u)
        by_type.setdefault(ptype, []).append(u)

    priority_order = ["product", "pricing", "service", "category", "contact",
                      "location", "about", "documentation", "article", "other"]
    selected_urls = []
    for t in priority_order:
        for u in by_type.get(t, [])[:3]:
            if len(selected_urls) >= max_pages - 1 or (deadline and time.time() >= deadline):
                break
            selected_urls.append(u)
        if len(selected_urls) >= max_pages - 1 or (deadline and time.time() >= deadline):
            break

    for u in selected_urls:
        if deadline and time.time() >= deadline:
            inv["limitations"].append("Inventory crawl truncated when acquisition time budget was reached.")
            break
        p_status, p_html, p_headers, _ = safe_fetch(u, timeout=8, max_bytes=2*1024*1024)
        if p_html and is_html_response(p_headers, p_html):
            seen_urls.add(u.rstrip("/"))
            inv["pages"].append({
                "url": u,
                "status": p_status,
                "resource_type": "html",
                "content_type": p_headers.get("content-type", "text/html"),
                "page_type": classify_page(u, _extract_title(p_html)),
                "title": _extract_title(p_html),
                "word_count": _visible_words(p_html),
                "html": p_html
            })

    inv["elapsed_seconds"] = round(time.time() - start, 1)
    stats = {
        "homepage_reachable": True,
        "html_pages_sampled": len(inv["pages"]),
        "sitemaps_found": len(inv["infrastructure"]["sitemaps_discovered"]),
        "sitemaps_processed": inv["infrastructure"]["sitemaps_processed"],
        "urls_discovered": inv["infrastructure"]["urls_extracted"],
        "same_origin_urls": inv["infrastructure"]["same_origin_urls"],
        "elapsed_seconds": inv["elapsed_seconds"],
        "page_types": {t: sum(1 for p in inv["pages"] if p.get("page_type") == t)
                       for t in {p.get("page_type") for p in inv["pages"] if p.get("page_type")}}
    }
    return inv, stats


def main():
    parser = argparse.ArgumentParser(description="Shared site inventory acquisition utility.")
    parser.add_argument("--site", required=True, help="Target website URL or domain")
    parser.add_argument("--output", "-o", help="Path to save inventory JSON")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    args = parser.parse_args()

    s = args.site.strip()
    if not (s.startswith("http://") or s.startswith("https://")):
        base_url = f"https://{s.split('/')[0]}"
    else:
        parts = s.split("://", 1)
        base_url = f"{parts[0]}://{parts[1].split('/')[0]}"

    inv, stats = build_inventory(base_url)
    out_data = inv if inv else {"homepage_reachable": False, "error": stats.get("error")}
    out_json = json.dumps(out_data, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json + "\n")
    else:
        print(out_json)


if __name__ == "__main__":
    main()

