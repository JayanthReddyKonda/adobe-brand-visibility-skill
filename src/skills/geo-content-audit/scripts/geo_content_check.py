#!/usr/bin/env python3
"""
geo_content_check.py - Generative Engine Optimization (GEO) audit layer.

Evaluates pages for AI-friendly text structures: statistical density,
answer blocks, and data tables.
"""
import sys
import os
import json
import argparse
import re
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


from safe_fetch import safe_fetch

QUESTION_RE = re.compile(r"^(what|why|how|when|where|who|which|can|does|is|are)\b|\?$", re.I)
_WORD_RE = re.compile(r"\b\w+\b")
_STAT_RE = re.compile(
    r"\b(?:"
    r"\d+(?:[.,]\d+)?\s*%"
    r"|\$\s*\d+(?:[.,]\d+)?[KMBkmb]?"
    r"|\d+(?:[.,]\d+)?\s*[×x]"
    r"|\d{2,}(?:[.,]\d+)?"
    r"|\d+\s*(?:million|billion|thousand)"
    r"|\d+(?:[.,]\d+)?\s*[KMB]"
    r")\b",
    re.IGNORECASE,
)

class GEODOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.text_blocks = []
        self.current_tag = None
        self.tables = 0
        self.lists = 0
        self.headings = []
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
        if self.current_tag in ("script", "style"):
            self.in_script = True
        elif self.current_tag == "table":
            self.tables += 1
        elif self.current_tag in ("ul", "ol", "dl"):
            self.lists += 1

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = False
        self.current_tag = None

    def handle_data(self, data):
        if not self.in_script and data.strip():
            txt = data.strip()
            self.text_blocks.append(txt)
            if self.current_tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self.headings.append(txt)

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

    # We only audit 'product_detail' or 'article' pages for GEO optimizations
    target_pages = [p for p in html_pages if p.get("page_type") in ("product_detail", "article", "pricing")]

    for p in target_pages:
        url = p.get("url")
        html = p.get("html")
        ptype = p.get("page_type")
        
        parser = GEODOMParser()
        try:
            parser.feed(html)
        except Exception:
            pass
        
        full_text = " ".join(parser.text_blocks)
        
        # P0 Semantic GEO: AutoGEO Metrics
        
        # 1. In-Depth Mechanisms ('how', 'why', 'because', 'therefore')
        mechanism_words = ['how', 'why', 'because', 'therefore', 'allows', 'enables', 'mechanism', 'results in']
        import re; depth_score = sum(1 for w in mechanism_words if re.search(rf"\b{w}\b", full_text.lower()))
        
        if depth_score < 2:
            findings.append({
                "category": "content",
                "title": "Content lacks explanatory depth mechanisms",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "The page fails to provide in-depth mechanistic explanations ('how' and 'why'), which Generative Engines heavily prioritize.",
                "cause_family": "CONTENT.SHALLOW_COVERAGE",
                "id": "MISSING_IN_DEPTH_MECHANISMS", "cause_id": "MISSING_IN_DEPTH_MECHANISMS",
                "evidence": f"Page {url} lacks causal conjunctions or explanatory depth markers.",
                "impact": "Generative Engines prefer to cite sources that offer deep explanatory context rather than surface-level statements.",
                "suggested_action": {
                    "summary": "Expand the content to explain the underlying mechanisms and context ('how' and 'why').",
                    "priority": "medium"
                }
            })
            
        # 2. Specific Evidence (digits, quantifiable facts)
        has_evidence = len(_STAT_RE.findall(full_text)) > 0
        if not has_evidence:
            recommendations.append({
                "title": "Substantiate content with quantifiable evidence and statistics",
                "category": "content",
                "rationale": f"Substantiate claims on {url} with specific, verifiable data, statistics, or named examples to improve AutoGEO preference.",
                "summary": f"Substantiate claims on {url} with specific, verifiable data, statistics, or named examples to improve AutoGEO preference.",
                "suggested_action": "Incorporate verifiable statistics, benchmark numbers, or quantifiable metrics."
            })

        
        
        
        has_questions = any(QUESTION_RE.search(h) for h in parser.headings)
        
        # P0-6 & P0-7: Advisory GEO Metrics
        if ptype == "product_detail" and parser.tables == 0 and parser.lists == 0:
            recommendations.append({
                "title": "Structure product specifications in semantic tables or lists",
                "category": "content",
                "rationale": f"Product page {url} contains no semantic tables or lists.",
                "summary": f"Product page {url} contains no semantic tables or lists. If material attributes are genuinely hard to isolate, structuring them may aid deterministic extraction.",
                "suggested_action": "Add structured <table>, <dl>, or <ul> elements for material specifications."
            })

        # Articles / Information pages need statistical density and clear answer blocks
        if ptype == "article":
            
            if not has_questions:
                recommendations.append({
                    "title": "Incorporate Direct Question Headings (FAQ formatting)",
                    "category": "content",
                    "rationale": f"Article {url} lacks explicit question headings (H2/H3). Adding question-oriented headings can serve as an optimization opportunity for conversational queries.",
                    "suggested_action": "Add explicit 'What is...', 'How to...', or 'Why...' headings followed immediately by concise answer paragraphs."
                })
                
    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations
    }

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
                "pages": [{
                    "url": args.site,
                    "status": 200,
                    "content_type": "text/html",
                    "page_type": "article",
                    "html": html
                }]
            }
        else:
            inv = {"site": args.site, "pages": []}
    
    from urllib.parse import urlparse
    res = audit(args.site, urlparse(args.site).netloc, inv)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()