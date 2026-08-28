#!/usr/bin/env python3
"""
freshness_check.py - Audits fact freshness, update timestamps, and entity corroboration.
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
    findings = []
    parser = FreshnessAnalyzer()
    try:
        parser.feed(html_str)
    except Exception as e:
        sys.stderr.write(f"Freshness HTML parse warning: {e}\n")

    full_text = " ".join(parser.text_content)

    # 1. Check Copyright Year
    copyright_matches = re.findall(r'(?:©|&copy;|copyright)\s*(?:[0-9]{4}\s*[-–]\s*)?([0-9]{4})', full_text, re.IGNORECASE)
    if copyright_matches:
        try:
            latest_c_year = max(int(y) for y in copyright_matches if 1990 <= int(y) <= CURRENT_YEAR + 1)
            if latest_c_year < CURRENT_YEAR - 1:
                findings.append({
                    "id": "FC-COPYRIGHT-STALE",
                    "title": "Outdated copyright year detected",
                    "severity": "medium",
                    "evidence": f"Visible copyright notice shows '{latest_c_year}', which is older than {CURRENT_YEAR - 1}. Stale dates signal abandoned maintenance to AI models.",
                    "suggested_action": {
                        "summary": f"Update footer copyright year to {CURRENT_YEAR} and consider using a dynamic year snippet.",
                        "priority": "medium"
                    }
                })
        except ValueError:
            pass

    # 2. Check Modified Timestamps
    has_modified_meta = any(k in parser.meta_tags for k in [
        "article:modified_time", "og:updated_time", "last-modified", "date"
    ])
    
    # 3. Check JSON-LD for sameAs and dateModified
    has_same_as = False
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
                        has_same_as = True
                        val = obj["sameAs"]
                        if isinstance(val, list):
                            same_as_links.extend(val)
                        elif isinstance(val, str):
                            same_as_links.append(val)
                    if "dateModified" in obj or "datePublished" in obj:
                        has_date_modified = True
        except Exception:
            pass

    if not has_modified_meta and not has_date_modified:
        findings.append({
            "id": "FC-DATE-MODIFIED-MISSING",
            "title": "Missing content modification timestamps",
            "severity": "medium",
            "evidence": "No 'dateModified' or 'article:modified_time' metadata found to communicate content freshness.",
            "suggested_action": {
                "summary": "Expose ISO 8601 modification dates in OpenGraph and JSON-LD markup.",
                "priority": "medium"
            }
        })

    # 4. Check Entity Corroboration (sameAs links)
    if not has_same_as or not same_as_links:
        findings.append({
            "id": "FC-ENTITY-SAMEAS-MISSING",
            "title": "Missing sameAs entity corroboration links in structured data",
            "severity": "high",
            "evidence": f"Structured data on {url_or_domain} lacks 'sameAs' links to Wikidata, Crunchbase, or verified social profiles, increasing entity ambiguity for AI assistants.",
            "suggested_action": {
                "summary": "Add authoritative 'sameAs' URLs in Organization JSON-LD linking to Wikidata and corporate registry profiles.",
                "priority": "high"
            }
        })

    return findings

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

def main():
    parser = argparse.ArgumentParser(description="Audit fact freshness and entity corroboration.")
    parser.add_argument("--site", help="URL or domain to audit")
    parser.add_argument("--file", help="Path to local HTML file to inspect")
    args = parser.parse_args()

    findings = []

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            html = f.read()
        findings.extend(audit_freshness(html, args.file))

    if args.site:
        site_clean = args.site if args.site.startswith("http") else f"https://{args.site}"
        status, html = fetch_url(site_clean)
        if html:
            findings.extend(audit_freshness(html, site_clean))

    print(json.dumps(findings, indent=2))

if __name__ == "__main__":
    main()

