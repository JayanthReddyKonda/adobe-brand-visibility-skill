#!/usr/bin/env python3
"""
fact_consistency_check.py - Audits fact freshness, update timestamps, and entity corroboration.
Zero external dependencies (uses Python standard library).
"""

import sys
import os
import re
import json
import argparse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser

CURRENT_YEAR = datetime.now().year

class FreshnessAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_json_ld = False
        self.json_ld_contents = []
        self.meta_tags = {}
        self.text_content = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower == "script":
            self.in_script = True
            if "application/ld+json" in attr_dict.get("type", "").lower():
                self.in_json_ld = True
        elif tag_lower == "meta":
            prop = attr_dict.get("property", attr_dict.get("name", "")).lower()
            content = attr_dict.get("content", "")
            if prop and content:
                self.meta_tags[prop] = content

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            self.in_script = False
            self.in_json_ld = False

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())
        elif not self.in_script:
            txt = data.strip()
            if txt:
                self.text_content.append(txt)

def audit_freshness(html_str, url_or_domain):
    """Returns (findings, recommendations). Only evidence-backed defects are
    findings; improvement opportunities are returned as recommendations."""
    findings = []
    recommendations = []
    parser = FreshnessAnalyzer()
    try:
        parser.feed(html_str)
    except Exception as e:
        sys.stderr.write(f"Freshness HTML parse warning: {e}\n")

    full_text = " ".join(parser.text_content)

    result = {
        "copyright_year": None,
        "org_name": None,
        "has_dates": False,
        "has_same_as": False,
        "word_count": len(full_text.split()),
    }

    # 1. Copyright year (weak maintenance signal -> low severity at most)
    copyright_matches = re.findall(r'(?:©|&copy;|copyright)\s*(?:[0-9]{4}\s*[-–]\s*)?([0-9]{4})', full_text, re.IGNORECASE)
    if copyright_matches:
        try:
            latest_c_year = max(int(y) for y in copyright_matches if 1990 <= int(y) <= CURRENT_YEAR + 1)
            result["copyright_year"] = latest_c_year
            # A copyright year alone is NOT a freshness finding (Google's
            # sitemap guidance: lastmod/years are not proof of content
            # staleness). The year is retained only for cross-page
            # contradiction detection below.
        except ValueError:
            pass

    # 2. Extract organization name for cross-page comparison
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_str, re.IGNORECASE)
    if title_match:
        result["org_name"] = title_match.group(1).strip()

    # 3. Modification timestamps (weak signal -> low, only for content pages)
    has_modified_meta = any(k in parser.meta_tags for k in
                            ["article:modified_time", "og:updated_time", "last-modified"])
    has_date_modified = False
    same_as_links = []

    for raw_json in parser.json_ld_contents:
        if not raw_json:
            continue
        try:
            data = json.loads(raw_json)
            objects = data if isinstance(data, list) else [data]
            for obj in objects:
                if isinstance(obj, dict):
                    if "sameAs" in obj:
                        result["has_same_as"] = True
                        val = obj["sameAs"]
                        if isinstance(val, list):
                            same_as_links.extend(val)
                        elif isinstance(val, str):
                            same_as_links.append(val)
                    if "dateModified" in obj or "datePublished" in obj:
                        has_date_modified = True
                        result["has_dates"] = True
        except Exception:
            pass
    result["has_dates"] = result["has_dates"] or has_modified_meta

    if not result["has_dates"] and result["word_count"] >= 100:
        # Missing timestamps on a content-bearing page: low-severity signal.
        findings.append({
            "id": "FC-DATE-MODIFIED-MISSING",
            "title": "No freshness timestamps exposed",
            "severity": "low",
            "evidence": f"Page carries {result['word_count']} words of content but exposes no 'dateModified', 'article:modified_time', or equivalent. AI assistants cannot judge how current the information is; this is a signal gap, not proof of stale content.",
            "suggested_action": {
                "summary": "Expose ISO 8601 modification dates via OpenGraph ('article:modified_time') and JSON-LD ('dateModified') on content pages.",
                "priority": "low"
            }
        })

    # 4. Entity corroboration: absence of sameAs alone is NOT evidence of
    #    entity ambiguity, so it is an optional improvement, not a defect.
    if not result["has_same_as"] and result["word_count"] >= 30:
        recommendations.append({
            "title": "Add sameAs entity links to structured data",
            "rationale": f"No 'sameAs' links to authoritative profiles (Wikidata, social, registries) were found on {url_or_domain}. If competing entities share the brand name, this raises entity-disambiguation risk; absent such ambiguity it is simply a strengthening measure.",
            "suggested_action": "Add 'sameAs' URLs to the Organization JSON-LD pointing at Wikidata, Crunchbase, and official social profiles."
        })

    return findings, recommendations, result

def fetch_url(url, timeout=5):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        sys.stderr.write(f"Fetch failed for {url}: {e}\n")
        return None, None

def extract_internal_links(html_str, base_url, limit=2):
    """Extract a few same-domain links for cross-page consistency checks."""
    links = []
    base_domain = "/".join(base_url.split("/")[:3])
    for match in re.finditer(r'<a[^>]+href=["\']([^"\'#]+)["\']', html_str, re.IGNORECASE):
        href = match.group(1)
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        if href.startswith("/"):
            links.append(base_domain + href)
        elif href.startswith(base_domain):
            links.append(href)
        if len(links) >= limit:
            break
    return links

def normalize_price(raw):
    """Normalize a price string to comparable digits (e.g. '₹5,499.00' -> '5499')."""
    digits = re.sub(r"[^\d]", "", raw.split(".")[0])
    return digits or None


def extract_facts(html_str, url):
    """Extract comparable first-party facts from one page (the fact ledger).

    Only facts that are objectively comparable are extracted: prices,
    contact emails, and phone numbers. Organizational/price claims that
    require interpretation are deliberately excluded (they cannot be
    adjudicated deterministically without generating false positives).
    """
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_str, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    facts = {"price": [], "email": [], "phone": []}

    # Prices: currency symbol/code followed by an amount.
    for m in re.finditer(
        r"(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?([\d][\d,\.]*)", text, re.IGNORECASE
    ):
        norm = normalize_price(m.group(1))
        if norm and len(norm) >= 2:
            facts["price"].append(norm)

    # Emails on the page (first-party contact facts).
    for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.-]+", html_str):
        addr = m.group(0).strip(".").lower()
        if not addr.endswith((".png", ".jpg", ".gif", ".webp", ".js", ".css")):
            facts["email"].append(addr)

    # Phone numbers: intl-format sequences of 8+ digits with separators.
    for m in re.finditer(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,4}\d{2,4}", text):
        digits = re.sub(r"\D", "", m.group(0))
        if 8 <= len(digits) <= 15:
            facts["phone"].append(digits)

    return {"url": url, "facts": {k: sorted(set(v)) for k, v in facts.items() if v}}


def fact_ledger_check(page_facts):
    """Cross-page fact ledger: a finding only when the SAME fact key holds
    conflicting values across first-party pages (a verified inconsistency,
    not an absence)."""
    findings = []
    ledger = {}
    for page in page_facts:
        for fact_key, values in page["facts"].items():
            for value in values:
                ledger.setdefault(fact_key, {}).setdefault(value, []).append(page["url"])

    label = {"price": "Price", "email": "Contact email", "phone": "Phone number"}
    for fact_key, value_map in ledger.items():
        if len(value_map) < 2:
            continue
        detail = "; ".join(
            f"{v} on {', '.join(urls)}" for v, urls in sorted(value_map.items())
        )
        n_urls = len({u for urls in value_map.values() for u in urls})
        findings.append({
            "category": "fact-consistency",
            "title": f"{label.get(fact_key, fact_key)} differs across first-party pages",
            "severity": "medium" if fact_key != "price" else "high",
            "confidence": "high" if fact_key == "price" else "medium",
            "root_cause": f"Multiple distinct {fact_key} values are published on the same site, so a retrieval system can extract contradictory facts for the same entity.",
            "impact": f"AI assistants and users may quote an outdated or wrong {fact_key}; conflicting evidence also weakens corroboration.",
            "evidence": f"{n_urls} page(s) carry conflicting values: {detail}",
            "suggested_action": {
                "summary": f"Establish one canonical {fact_key} and synchronize it across all pages and structured data; remove or update stale references.",
                "priority": "medium" if fact_key != "price" else "high",
                "verification": f"Re-crawl the affected URLs and confirm a single {fact_key} value appears everywhere."
            }
        })
    return findings

    return links


def cross_page_check(home_result, home_url, fetched_pages):
    """Compare identity/maintenance signals across pages. Only a verified
    contradiction is a finding; missing signals never are."""
    findings = []
    for page_url, page_result in fetched_pages:
        # Copyright-year contradiction across pages of the same site
        y1, y2 = home_result.get("copyright_year"), page_result.get("copyright_year")
        if y1 and y2 and y1 != y2:
            findings.append({
                "id": "FC-CROSS-COPYRIGHT",
                "title": "Inconsistent copyright years across pages",
                "severity": "medium",
                "evidence": f"'{home_url}' shows copyright {y1} while '{page_url}' shows {y2}. Contradictory maintenance signals on the same site confuse freshness inference.",
                "suggested_action": {
                    "summary": "Render the copyright year dynamically so it is identical across all pages.",
                    "priority": "medium"
                }
            })
    return findings


def main():
    parser = argparse.ArgumentParser(description="Audit fact freshness and entity corroboration.")
    parser.add_argument("--site", help="URL or domain to audit")
    parser.add_argument("--file", help="Path to local HTML file to inspect")
    parser.add_argument("--no-cross-page", action="store_true", help="Skip cross-page consistency fetching")
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON (from audit-orchestrator); its pages replace independent fetches")
    args = parser.parse_args()

    inv = None
    if getattr(args, "inventory", None) and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None

    findings = []
    recommendations = []

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            html = f.read()
        f_findings, f_recs, _ = audit_freshness(html, args.file)
        findings.extend(f_findings)
        recommendations.extend(f_recs)

    if args.site:
        site_clean = args.site if args.site.startswith("http") else f"https://{args.site}"
        # Shared inventory: use the orchestrator's evidence snapshot when
        # provided (homepage + bounded priority pages, no re-fetching).
        if inv is not None:
            home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
            html = home.get("html") if home else None
        else:
            status, html = fetch_url(site_clean)
        if html:
            f_findings, f_recs, home_result = audit_freshness(html, site_clean)
            findings.extend(f_findings)
            recommendations.extend(f_recs)

            # Cross-page consistency: verify facts across the shared page set.
            pages = []
            if not args.no_cross_page:
                fetched = []
                page_facts = [extract_facts(html, site_clean)]
                if inv is not None:
                    pages = [(p["url"], p["html"]) for p in inv.get("pages", [])
                             if p.get("html") and p.get("page_type") != "homepage"]
                else:
                    pages = []
                    for link in extract_internal_links(html, site_clean):
                        p_status, p_html = fetch_url(link)
                        if p_html:
                            pages.append((link, p_html))
                for link, p_html in pages[:8]:
                    _, _, p_result = audit_freshness(p_html, link)
                    fetched.append((link, p_result))
                    page_facts.append(extract_facts(p_html, link))
                findings.extend(cross_page_check(home_result, site_clean, fetched))
                # Fact ledger: conflicting values for the same fact across pages.
                findings.extend(fact_ledger_check(page_facts))
            print(json.dumps({"status": "ok", "findings": findings,
                              "recommendations": recommendations,
                              "coverage": {"pages_checked": 1 + (len(pages) if not args.no_cross_page else 0),
                                           "source": "shared-inventory" if inv is not None else "independent-fetch"},
                              "limitations": (["fact extraction covers raw HTML text and JSON-LD only"] if inv is not None else [])},
                             indent=2))
        else:
            print(json.dumps({"status": "inconclusive", "findings": [],
                              "recommendations": [],
                              "error": f"could not reach {site_clean} (network unreachable or blocked)"},
                             indent=2))
        return
    print(json.dumps({"status": "ok" if (findings or recommendations or args.file) else "inconclusive",
                      "findings": findings, "recommendations": recommendations}, indent=2))

if __name__ == "__main__":
    main()

