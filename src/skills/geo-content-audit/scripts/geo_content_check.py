#!/usr/bin/env python3
"""
geo_content_check.py - Generative Engine Optimization (GEO) audit layer.

Evaluates pages for AI-friendly text structures based on empirical Generative Engine
Optimization research (Princeton KDD 2024, CMU AutoGEO, and C-SEO Bench):
  - Mechanistic causal depth ('how', 'why', 'because', 'therefore', 'enables')
  - Quantifiable statistical density (percentages, metrics, benchmark figures)
  - Primary source citations & outbound authority anchors
  - Author credentials & E-E-A-T signals (MD, PhD, Dr., bylines)
  - Direct answer leads (inverted pyramid 40-60w) & FAQ formatting
  - Semantic tables, definition lists, and passage chunk optimization
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from safe_fetch import safe_fetch

QUESTION_RE = re.compile(r"^(what|why|how|when|where|who|which|can|does|is|are)\b|\?$", re.IGNORECASE)
_WORD_RE = re.compile(r"\b\w+\b")
_STAT_RE = re.compile(
    r"\b(?:"
    r"\d+(?:[.,]\d+)?\s*%"
    r"|\$\s*\d+(?:[.,]\d+)?[KMBkmb]?"
    r"|€\s*\d+(?:[.,]\d+)?[KMBkmb]?"
    r"|£\s*\d+(?:[.,]\d+)?[KMBkmb]?"
    r"|₹\s*\d+(?:[.,]\d+)?[KMBkmb]?"
    r"|\d+(?:[.,]\d+)?\s*[×x]"
    r"|\d{2,}(?:[.,]\d+)?"
    r"|\d+\s*(?:million|billion|thousand)"
    r"|\d+(?:[.,]\d+)?\s*[KMB]"
    r")\b",
    re.IGNORECASE,
)
_CREDENTIAL_RE = re.compile(
    r"\b(Dr\.|MD|PhD|MBA|Prof\.|Professor|M\.S\.|B\.S\.|Lead Researcher|Chief Scientist)\b", re.IGNORECASE
)
_FLUFF_RE = re.compile(
    r"\b(delve|delving|tapestry|game-changer|testament to|multifaceted|beacon of|revolutionize|spearheading|unleash)\b",
    re.IGNORECASE,
)

AUTHORITATIVE_DOMAINS = {
    "doi.org",
    "wikipedia.org",
    "nih.gov",
    "arxiv.org",
    "cdc.gov",
    "nature.com",
    "science.org",
    "ieee.org",
    "acm.org",
    "github.com",
    "w3.org",
    "schema.org",
}


class GEODOMParser(HTMLParser):
    def __init__(self, base_domain=""):
        super().__init__()
        self.base_domain = (base_domain or "").lower()
        self.in_script = False
        self.text_blocks = []
        self.paragraphs = []
        self.current_tag = None
        self.current_p_text = []
        self.tables = 0
        self.lists = 0
        self.headings = []
        self.outbound_citations = []
        self.author_bylines = []
        self.quotes_count = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()
        self.current_tag = t

        if t in ("script", "style"):
            self.in_script = True
        elif t == "table":
            self.tables += 1
        elif t in ("ul", "ol", "dl"):
            self.lists += 1
        elif t == "p":
            self.current_p_text = []
        elif t == "a" and attr_dict.get("href"):
            href = attr_dict["href"]
            if href.startswith("http"):
                parsed = urlparse(href)
                host = parsed.netloc.lower()
                if host and host != self.base_domain and not host.endswith("." + self.base_domain):
                    self.outbound_citations.append(href)

        # Check for author markup
        rel = attr_dict.get("rel", "").lower()
        cls = attr_dict.get("class", "").lower()
        itemprop = attr_dict.get("itemprop", "").lower()
        if "author" in rel or "author" in cls or "byline" in cls or itemprop == "author":
            self.author_bylines.append(attr_dict.get("content", "") or tag)

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = False
        elif t == "p":
            ptxt = " ".join(self.current_p_text).strip()
            if ptxt:
                self.paragraphs.append(ptxt)
            self.current_p_text = []
        self.current_tag = None

    def handle_data(self, data):
        if not self.in_script and data.strip():
            txt = data.strip()
            self.text_blocks.append(txt)
            if self.current_tag == "p":
                self.current_p_text.append(txt)
            if self.current_tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self.headings.append(txt)
            if '"' in data or "“" in data or "”" in data:
                self.quotes_count += 1


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def audit(base, domain, inv=None, state_file=None):
    findings = []
    recommendations = []
    observations = []

    if not inv or not inv.get("pages"):
        return {"status": "inconclusive", "findings": [], "recommendations": []}

    html_pages = [p for p in inv["pages"] if p.get("html")]
    if not html_pages:
        return {"status": "inconclusive", "findings": [], "recommendations": []}

    target_pages = [p for p in html_pages if p.get("page_type") in ("product_detail", "article", "pricing", "about")]

    for p in target_pages:
        url = p.get("url")
        html = p.get("html")
        ptype = p.get("page_type")

        parser = GEODOMParser(base_domain=domain)
        try:
            parser.feed(html)
        except Exception:
            pass

        full_text = " ".join(parser.text_blocks)
        total_words = _word_count(full_text)

        # 1. Princeton Vector: In-Depth Mechanisms ('how', 'why', 'because', 'therefore') - +40.3% boost
        mechanism_words = [
            "how",
            "why",
            "because",
            "therefore",
            "allows",
            "enables",
            "mechanism",
            "results in",
            "due to",
            "consequently",
        ]
        depth_score = sum(1 for w in mechanism_words if re.search(rf"\b{w}\b", full_text.lower()))

        if depth_score < 2:
            findings.append(
                {
                    "category": "content",
                    "title": "Content lacks explanatory depth mechanisms",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "The page fails to provide in-depth mechanistic explanations ('how' and 'why'), which Generative Engines heavily prioritize.",
                    "cause_family": "CONTENT.SHALLOW_COVERAGE",
                    "id": "MISSING_IN_DEPTH_MECHANISMS",
                    "cause_id": "MISSING_IN_DEPTH_MECHANISMS",
                    "evidence": f"Page {url} lacks causal conjunctions or explanatory depth markers (depth score: {depth_score}/10).",
                    "impact": "Generative Engines prefer to cite sources that offer deep explanatory context rather than surface-level assertions.",
                    "suggested_action": {
                        "summary": "Expand the content to explain the underlying mechanisms and context ('how' and 'why').",
                        "technical_fix": "Incorporate FAQ structured schema explaining product value propositions.",
                        "creative_fix": "Rewrite product descriptions to use causal conjunctions ('because', 'due to', 'enables').",
                        "priority": "medium",
                        "verification": "Scan text for causal depth markers and ensure depth score >= 3.",
                    },
                }
            )

        # 2. Princeton Vector: Quantifiable Evidence & Statistics - +37.1% boost
        stat_matches = _STAT_RE.findall(full_text)
        if len(stat_matches) == 0 and total_words > 100:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.STATISTICAL_EVIDENCE.001",
                    "title": "Substantiate content with quantifiable evidence and statistics",
                    "category": "content",
                    "summary": f"Substantiate claims on {url} with specific, verifiable data, statistics, or named benchmark metrics (+37% GEO citation boost).",
                    "priority": "medium",
                    "technical_fix": "Add verified numerical benchmarks and percentage metrics into specification tables.",
                    "creative_fix": "Include quantified performance gains or case study statistics in body paragraphs.",
                    "verification": "Confirm numbers and percentage metrics are visible in the body text.",
                }
            )

        # 3. Princeton Vector: Outbound Authority Citations - +115% citation boost
        if ptype == "article" and total_words > 200:
            has_auth_citation = any(
                any(ad in c.lower() for ad in AUTHORITATIVE_DOMAINS) or ".edu" in c.lower() or ".gov" in c.lower()
                for c in parser.outbound_citations
            )
            if not has_auth_citation:
                recommendations.append(
                    {
                        "id": "PROACTIVE.GEO.AUTHORITY_CITATIONS.001",
                        "title": "Cite primary authoritative external sources",
                        "category": "content",
                        "summary": f"Article {url} lacks outbound links to primary sources (academic papers, standards bodies, government data). Citing primary sources increases LLM citation probability by +115%.",
                        "priority": "low",
                        "technical_fix": "Add outbound anchor links pointing to DOI papers, Wikipedia, or official standards.",
                        "creative_fix": "Attribute key industry claims to recognized research studies or authoritative datasets.",
                        "verification": "Verify outbound citation links resolve with HTTP 200.",
                    }
                )

        # 4. E-E-A-T Vector: Author Byline & Credentials - +40% boost
        if ptype == "article" and total_words > 150:
            has_credentials = bool(_CREDENTIAL_RE.search(full_text)) or len(parser.author_bylines) > 0
            if not has_credentials:
                recommendations.append(
                    {
                        "id": "PROACTIVE.GEO.AUTHOR_CREDENTIALS.001",
                        "title": "Add author byline with professional credentials",
                        "category": "content",
                        "summary": f"Article {url} lacks named author credentials (MD, PhD, Dr., job title). Named credentials increase AI engine trust weighting.",
                        "priority": "low",
                        "technical_fix": "Embed Schema.org Author Person markup with jobTitle and honorificSuffix.",
                        "creative_fix": "Display an author byline box with bio, credentials, and published/updated dates.",
                        "verification": "Verify author byline is visible and represented in JSON-LD.",
                    }
                )

        # 5. AutoGEO Vector: Direct Answer Lead & Question Headings
        has_questions = any(QUESTION_RE.search(h) for h in parser.headings)
        if ptype == "article" and not has_questions and total_words > 150:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.QUESTION_HEADINGS.001",
                    "title": "Incorporate Direct Question Headings (FAQ / Q&A formatting)",
                    "category": "content",
                    "summary": f"Article {url} lacks question-oriented headings (H2/H3). Question headings match conversational user search intent.",
                    "priority": "low",
                    "technical_fix": "Structure key sections under <h2>What is...</h2> and <h2>How does...</h2> headings.",
                    "creative_fix": "Place concise 40-60 word direct answers immediately below question headings.",
                    "verification": "Verify question headings and direct answer leads are present in markup.",
                }
            )

        # 6. Structured Content Vector: Tables and Lists
        if ptype == "product_detail" and parser.tables == 0 and parser.lists == 0:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.STRUCTURED_TABLES.001",
                    "title": "Structure product specifications in semantic tables or lists",
                    "category": "content",
                    "summary": f"Product page {url} contains no semantic tables or lists. Structuring specifications in <table> or <dl> accelerates LLM fact extraction.",
                    "priority": "low",
                    "technical_fix": "Replace comma-separated feature text with semantic <table> and <ul> elements.",
                    "creative_fix": "Format comparison attributes into scannable feature rows.",
                    "verification": "Confirm <table> or <dl> elements are rendered in the HTML source.",
                }
            )

        # 7. AI Fluff Penalty Warning
        fluff_matches = _FLUFF_RE.findall(full_text)
        if len(fluff_matches) >= 3:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.REDUCE_FLUFF.001",
                    "title": "Replace promotional filler and buzzwords with concrete facts",
                    "category": "content",
                    "summary": f"Page {url} contains repetitive AI buzzword intensifiers ({', '.join(set(fluff_matches[:3]))}). Replacing filler with concrete metrics improves citation credibility.",
                    "priority": "low",
                    "technical_fix": "Audit copy to remove empty intensifiers and focus on mechanistic details.",
                    "creative_fix": "Replace vague adjectives with specific technical parameters.",
                    "verification": "Confirm marketing fluff density is minimized across body text.",
                }
            )

    return {"status": "ok", "findings": findings, "recommendations": recommendations, "observations": observations}


def main():
    parser = argparse.ArgumentParser(description="Generative Engine Optimization (GEO) audit layer.")
    parser.add_argument("--site", required=True, help="Target website URL")
    parser.add_argument("--inventory", required=False, help="Path to pre-acquired site inventory JSON")
    parser.add_argument("--state", help="Path to global state JSON")
    parser.add_argument("--format", required=False, help="Output format (json)")
    args = parser.parse_args()

    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    else:
        status, html, _, _ = safe_fetch(args.site)
        if status == 200 and html:
            inv = {
                "site": args.site,
                "pages": [
                    {"url": args.site, "status": 200, "content_type": "text/html", "page_type": "article", "html": html}
                ],
            }
        else:
            inv = {"site": args.site, "pages": []}

    res = audit(args.site, urlparse(args.site).netloc, inv)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
