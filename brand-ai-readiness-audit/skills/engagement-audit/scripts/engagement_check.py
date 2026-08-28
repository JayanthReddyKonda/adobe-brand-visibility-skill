#!/usr/bin/env python3
"""
engagement_check.py - Audits on-site visitor orientation, heading hierarchies,
navigation structure, and summary readiness.
Zero external dependencies (uses Python standard library).
"""

import sys
import os
import re
import json
import argparse
import urllib.request
from html.parser import HTMLParser

class EngagementAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.in_heading = False
        self.current_heading_tag = None
        self.headings = []
        self.nav_links_count = 0
        self.in_nav = False
        self.total_anchors = 0
        self.paragraphs = []
        self.in_paragraph = False
        self.current_paragraph_text = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in ["script", "style"]:
            self.in_script = True
        elif tag_lower in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = True
            self.current_heading_tag = tag_lower
            self.current_heading_text = []
        elif tag_lower == "nav":
            self.in_nav = True
        elif tag_lower == "a":
            self.total_anchors += 1
            if self.in_nav:
                self.nav_links_count += 1
        elif tag_lower == "p":
            self.in_paragraph = True
            self.current_paragraph_text = []

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ["script", "style"]:
            self.in_script = False
        elif tag_lower in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = False
            if hasattr(self, "current_heading_text"):
                txt = " ".join(self.current_heading_text).strip()
                if txt:
                    self.headings.append((self.current_heading_tag, txt))
        elif tag_lower == "nav":
            self.in_nav = False
        elif tag_lower == "p":
            self.in_paragraph = False
            if hasattr(self, "current_paragraph_text"):
                ptxt = " ".join(self.current_paragraph_text).strip()
                if ptxt:
                    self.paragraphs.append(ptxt)

    def handle_data(self, data):
        if self.in_heading and hasattr(self, "current_heading_text"):
            self.current_heading_text.append(data.strip())
        elif self.in_paragraph and hasattr(self, "current_paragraph_text"):
            self.current_paragraph_text.append(data.strip())

def audit_engagement(html_str, url_or_domain):
    findings = []
    parser = EngagementAnalyzer()
    try:
        parser.feed(html_str)
    except Exception as e:
        sys.stderr.write(f"Engagement HTML parse warning: {e}\n")

    h1_tags = [text for tag, text in parser.headings if tag == "h1"]
    h2_tags = [text for tag, text in parser.headings if tag == "h2"]
    total_text = " ".join(parser.paragraphs)
    word_count = len(total_text.split())
    content_bearing = word_count >= 50

    # 1. H1 presence — contextual, not automatic.
    #    On a content-bearing page with no H1, orientation suffers; on an
    #    empty/CSR shell page the crawl-render skill already reports the
    #    rendering gap, so we do not double-penalize here.
    if len(h1_tags) == 0:
        if content_bearing:
            findings.append({
                "id": "ENG-H1-MISSING",
                "title": "No H1 heading on content-bearing page",
                "severity": "medium",
                "evidence": f"Page carries ~{word_count} words but has no <h1>. Other headings present: {len(h2_tags)}. AI summarizers and skimming visitors lack a single primary topic statement.",
                "suggested_action": {
                    "summary": "Add one prominent <h1> that states what the page/brand offers, above the fold.",
                    "priority": "medium"
                }
            })
    else:
        # H1 quality: does it communicate substance (information scent)?
        primary_h1 = h1_tags[0]
        if len(primary_h1.split()) < 3:
            findings.append({
                "id": "ENG-H1-VAGUE",
                "title": "H1 heading carries little information scent",
                "severity": "low",
                "evidence": f"The page's <h1> is '{primary_h1}' ({len(primary_h1.split())} words). Short, generic headings do not tell visitors or AI summarizers what the organization actually offers.",
                "suggested_action": {
                    "summary": "Rewrite the <h1> to state the offer concretely, e.g. '<Brand>: freshly roasted specialty coffee delivered monthly'.",
                    "priority": "low"
                }
            })

    # Note: multiple H1 elements are valid HTML5 and are NOT reported as a
    # defect; only their combined semantic clarity would matter, which
    # requires human/LLM judgment beyond deterministic scope.

    # 2. Heading Hierarchy & Information Scent
    if len(h2_tags) == 0 and len(parser.paragraphs) > 3:
        findings.append({
            "id": "ENG-H2-MISSING",
            "title": "Poor information scent: Absence of structured H2 subheadings",
            "severity": "medium",
            "evidence": "Page contains multiple body paragraphs without <h2> subheadings, creating a wall-of-text that degrades scannability.",
            "suggested_action": {
                "summary": "Organize features, use-cases, and proof points under descriptive <h2> headings.",
                "priority": "medium"
            }
        })

    # 3. Navigation — the real question is whether key destinations can be
    #    discovered, not whether a literal <nav> tag exists. Header/footer
    #    link menus (any anchors) satisfy discoverability.
    if parser.nav_links_count == 0 and parser.total_anchors < 3 and content_bearing:
        findings.append({
            "id": "ENG-NAV-MISSING",
            "title": "No navigational links discovered",
            "severity": "medium",
            "evidence": f"Page carries ~{word_count} words but contains only {parser.total_anchors} link(s) and no <nav> menu. Visitors referred by AI assistants cannot discover other key destinations (pricing, docs, about), raising bounce risk.",
            "suggested_action": {
                "summary": "Add a navigation menu with direct links to core destinations (Product, Pricing, Docs, About).",
                "priority": "medium"
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
    parser = argparse.ArgumentParser(description="Audit on-site visitor orientation, heading hierarchy, and summary readability.")
    parser.add_argument("--site", help="URL or domain to audit")
    parser.add_argument("--file", help="Path to local HTML file to inspect")
    args = parser.parse_args()

    findings = []

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            html = f.read()
        findings.extend(audit_engagement(html, args.file))

    if args.site:
        site_clean = args.site if args.site.startswith("http") else f"https://{args.site}"
        status, html = fetch_url(site_clean)
        if html:
            findings.extend(audit_engagement(html, site_clean))

    print(json.dumps(findings, indent=2))

if __name__ == "__main__":
    main()

