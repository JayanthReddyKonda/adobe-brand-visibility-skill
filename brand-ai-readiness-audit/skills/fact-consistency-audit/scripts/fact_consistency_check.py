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
            if latest_c_year < CURRENT_YEAR - 1:
                # A copyright year alone is not proof of stale *content*;
                # it is a weak maintenance signal.
                findings.append({
                    "id": "FC-COPYRIGHT-STALE",
                    "title": "Copyright year suggests minimal maintenance",
                    "severity": "low",
                    "evidence": f"Footer copyright shows '{latest_c_year}' while current year is {CURRENT_YEAR}. This is a weak signal on its own and does not prove content is stale, but it may read as an abandoned site.",
                    "suggested_action": {
                        "summary": f"Update the copyright year to {CURRENT_YEAR} (ideally render it dynamically). Verify volatile facts (pricing, dates, availability) are current.",
                        "priority": "low"
                    }
                })
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
    args = parser.parse_args()

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
        status, html = fetch_url(site_clean)
        if html:
            f_findings, f_recs, home_result = audit_freshness(html, site_clean)
            findings.extend(f_findings)
            recommendations.extend(f_recs)

            # Cross-page consistency: verify facts on a couple of internal pages.
            if not args.no_cross_page:
                fetched = []
                for link in extract_internal_links(html, site_clean):
                    p_status, p_html = fetch_url(link)
                    if p_html:
                        _, _, p_result = audit_freshness(p_html, link)
                        fetched.append((link, p_result))
                findings.extend(cross_page_check(home_result, site_clean, fetched))
            print(json.dumps({"status": "ok", "findings": findings,
                              "recommendations": recommendations}, indent=2))
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

