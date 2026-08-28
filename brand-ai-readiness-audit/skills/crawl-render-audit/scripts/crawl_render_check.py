#!/usr/bin/env python3
"""
crawl_render_check.py - Audits crawlability, rendering, DOM content extraction,
and Schema.org JSON-LD structured data for AI discoverability.
Zero external dependencies (uses Python standard library).
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error
from html.parser import HTMLParser

class DOMAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.in_json_ld = False
        self.current_script_type = ""
        self.json_ld_contents = []
        self.text_content = []
        self.images_total = 0
        self.images_without_alt = 0
        self.meta_robots = None
        self.canonical_url = None
        self.h1_tags = []
        self.spa_root_found = False

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower == "script":
            self.in_script = True
            stype = attr_dict.get("type", "").lower()
            if "application/ld+json" in stype:
                self.in_json_ld = True
        elif tag_lower == "style":
            self.in_style = True
        elif tag_lower == "img":
            self.images_total += 1
            if not attr_dict.get("alt", "").strip():
                self.images_without_alt += 1
        elif tag_lower == "meta":
            name = attr_dict.get("name", "").lower()
            if name == "robots":
                self.meta_robots = attr_dict.get("content", "")
        elif tag_lower == "link":
            rel = attr_dict.get("rel", "").lower()
            if rel == "canonical":
                self.canonical_url = attr_dict.get("href", "")
        elif tag_lower in ["div", "main", "section"]:
            elem_id = attr_dict.get("id", "").lower()
            if elem_id in ["root", "app", "__next", "__nuxt"]:
                self.spa_root_found = True

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == "script":
            self.in_script = False
            self.in_json_ld = False
        elif tag_lower == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())
        elif not self.in_script and not self.in_style:
            text = data.strip()
            if text:
                self.text_content.append(text)

def check_robots_txt(robots_text):
    findings = []
    if not robots_text:
        return findings

    ai_bots = ["gptbot", "claudebot", "perplexitybot", "google-extended", "bytespider", "ccbot"]
    blocked_bots = []

    lines = robots_text.splitlines()
    current_agent = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = [x.strip() for x in line.split(":", 1)]
            key_lower = key.lower()
            if key_lower == "user-agent":
                current_agent = val.lower()
            elif key_lower == "disallow" and val in ["/", "/*"]:
                if current_agent in ai_bots:
                    blocked_bots.append(current_agent)
                elif current_agent == "*":
                    blocked_bots.append("all (*)")

    if blocked_bots:
        findings.append({
            "id": "CR-ROBOTS-01",
            "title": "Robots.txt blocks AI crawler user-agents",
            "severity": "critical" if "all (*)" in blocked_bots or len(blocked_bots) >= 2 else "high",
            "evidence": f"robots.txt disallows access to bots: {', '.join(set(blocked_bots))}.",
            "suggested_action": {
                "summary": "Update robots.txt to allow indexing for verified AI search crawlers (GPTBot, ClaudeBot, PerplexityBot).",
                "priority": "critical"
            }
        })
    return findings

def audit_html_content(html_str, url_or_domain):
    findings = []
    parser = DOMAnalyzer()
    try:
        parser.feed(html_str)
    except Exception as e:
        sys.stderr.write(f"HTML parse warning: {e}\n")

    # 1. Check raw text volume (SPA / CSR gap)
    total_raw_text = " ".join(parser.text_content)
    word_count = len(total_raw_text.split())

    if word_count < 30 and parser.spa_root_found:
        findings.append({
            "id": "CR-RENDER-01",
            "title": "Client-side rendering gap: Raw HTML contains no substantive text",
            "severity": "high",
            "evidence": f"Raw HTML body contains only {word_count} words and an empty SPA root container. AI crawlers without JS execution will index an empty page.",
            "suggested_action": {
                "summary": "Implement Server-Side Rendering (SSR) or Static Site Generation (SSG) to render core text into initial HTML.",
                "priority": "high"
            }
        })

    # 2. Check JSON-LD structured data
    schemas_detected = []
    for raw_json in parser.json_ld_contents:
        if not raw_json:
            continue
        try:
            data = json.loads(raw_json)
            if isinstance(data, dict):
                stype = data.get("@type", "")
                if stype:
                    schemas_detected.append(stype)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "@type" in item:
                        schemas_detected.append(item["@type"])
        except Exception:
            findings.append({
                "id": "CR-SCHEMA-ERR",
                "title": "Malformed JSON-LD structured data syntax",
                "severity": "medium",
                "evidence": "Found a <script type='application/ld+json'> block containing invalid JSON.",
                "suggested_action": {
                    "summary": "Fix syntax errors in JSON-LD markup to enable schema parsing.",
                    "priority": "medium"
                }
            })

    if not schemas_detected:
        findings.append({
            "id": "CR-SCHEMA-01",
            "title": "Missing Schema.org JSON-LD structured data",
            "severity": "high",
            "evidence": f"No Schema.org structured data found on {url_or_domain}.",
            "suggested_action": {
                "summary": "Add Schema.org JSON-LD markup (e.g. Organization, Product, FAQPage) to explicitly declare brand entities.",
                "priority": "high"
            }
        })

    # 3. Check Image Alt Attributes (Facts trapped in images)
    if parser.images_total > 3 and parser.images_without_alt / parser.images_total > 0.5:
        findings.append({
            "id": "CR-IMG-ALT-01",
            "title": "Facts trapped in non-text images without alt descriptions",
            "severity": "medium",
            "evidence": f"{parser.images_without_alt} of {parser.images_total} images lack alt attributes, hiding visual claims from text-based AI models.",
            "suggested_action": {
                "summary": "Add descriptive alt attributes and semantic text captions for all diagrams, feature screenshots, and logos.",
                "priority": "medium"
            }
        })

    # 4. Check Meta Robots
    if parser.meta_robots and "noindex" in parser.meta_robots.lower():
        findings.append({
            "id": "CR-META-NOINDEX",
            "title": "Meta robots noindex tag detected",
            "severity": "critical",
            "evidence": f"Page contains <meta name='robots' content='{parser.meta_robots}'>, instructing all indexers to discard the page.",
            "suggested_action": {
                "summary": "Remove the 'noindex' directive from public marketing pages.",
                "priority": "critical"
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
    parser = argparse.ArgumentParser(description="Audit website crawlability, rendering, and Schema.org markup.")
    parser.add_argument("--site", help="URL or domain to audit")
    parser.add_argument("--file", help="Path to local HTML file to inspect")
    parser.add_argument("--robots", help="Path to local robots.txt file to inspect")
    args = parser.parse_args()

    findings = []

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            html = f.read()
        findings.extend(audit_html_content(html, args.file))

    if args.robots and os.path.exists(args.robots):
        with open(args.robots, "r", encoding="utf-8") as f:
            rtext = f.read()
        findings.extend(check_robots_txt(rtext))

    if args.site:
        site_clean = args.site if args.site.startswith("http") else f"https://{args.site}"
        domain_base = "/".join(site_clean.split("/")[:3])
        status, rtext = fetch_url(f"{domain_base}/robots.txt")
        if rtext:
            findings.extend(check_robots_txt(rtext))

        status, html = fetch_url(site_clean)
        if html:
            findings.extend(audit_html_content(html, site_clean))

    print(json.dumps(findings, indent=2))

if __name__ == "__main__":
    main()

