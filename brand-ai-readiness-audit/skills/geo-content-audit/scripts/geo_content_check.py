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

def audit(base, domain, inv=None):
    findings = []
    recommendations = []
    observations = []

    if not inv or not inv.get("pages"):
        return {"status": "not_run", "findings": [], "recommendations": []}

    html_pages = [p for p in inv["pages"] if p.get("html")]
    if not html_pages:
        return {"status": "not_run"}

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
        words = _word_count(full_text)
        stats = len(_STAT_RE.findall(full_text))
        
        density = (stats / max(words, 1)) * 100
        
        has_questions = any(QUESTION_RE.search(h) for h in parser.headings)
        
        # Product detail pages MUST have tables/lists for specs
        if ptype == "product_detail" and parser.tables == 0 and parser.lists == 0:
            findings.append({
                "category": "content",
                "title": "Product specifications lack LLM-optimized structured markup (tables/lists)",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "Product features are presented as unstructured prose without data tables or definition lists.",
                "cause_family": "CONTENT.RETRIEVAL_OPTIMIZATION",
                "cause_id": "POOR_DATA_DENSITY",
                "evidence": f"Product page {url} contains 0 tables or structured lists.",
                "impact": "Generative models strongly prefer tabular data for extracting technical specifications. Unstructured prose reduces extraction accuracy.",
                "suggested_action": {
                    "summary": "Convert prose product specifications into HTML <table> or <dl> formats.",
                    "priority": "medium"
                }
            })

        # Articles / Information pages need statistical density and clear answer blocks
        if ptype == "article":
            if density < 0.2:
                recommendations.append({
                    "title": "Improve GEO Statistical Density",
                    "category": "content",
                    "rationale": f"Article {url} has low statistical density ({density:.2f} stats per 100 words). Research indicates generative engines prefer data-dense claims.",
                    "suggested_action": "Incorporate explicit numeric statistics, pricing, or percentages to anchor LLM synthesis."
                })
            
            if not has_questions:
                recommendations.append({
                    "title": "Incorporate Direct Question Headings (FAQ formatting)",
                    "category": "content",
                    "rationale": f"Article {url} lacks explicit question headings (H2/H3). Question-and-answer pairs match LLM retrieval intents natively.",
                    "suggested_action": "Add explicit 'What is...', 'How to...', or 'Why...' headings followed immediately by 50-word answer paragraphs."
                })
                
    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--format", default="json")
    args = parser.parse_args()
    
    with open(args.inventory, "r", encoding="utf-8") as f:
        inv = json.load(f)
    
    res = audit(args.site, args.site, inv)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
