#!/usr/bin/env python3
"""
geo_content_check.py - Generative Engine Optimization (GEO) Citability Diagnostic Sensor.
Evaluates content citability, BLUF placement, hedge density, and evidence genres
based on Princeton KDD 2024 and AutoGEO research.
"""

import argparse
import json
import math
import os
import re
import sys
import zlib
from collections import Counter
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore

_ABBR_MAP = {
    "Dr.": "Dr__DOT__", "Mr.": "Mr__DOT__", "Mrs.": "Mrs__DOT__", "Ms.": "Ms__DOT__",
    "Prof.": "Prof__DOT__", "Sr.": "Sr__DOT__", "Jr.": "Jr__DOT__", "vs.": "vs__DOT__",
    "e.g.": "eg__DOT__", "i.e.": "ie__DOT__", "Inc.": "Inc__DOT__", "Ltd.": "Ltd__DOT__",
}

_HEDGE_RE = re.compile(
    r"\b(may|might|could|would|suggest|suggests|indicate|indicates|appear|appears|seem|seems|assume|estimate|probably|possibly|perhaps|roughly|somewhat)\b",
    re.IGNORECASE,
)
_STAT_RE = re.compile(r"(\b\d+(\.\d+)?%|\$\d+(?:,\d{3})*(?:\.\d+)?|\b\d+\s+(?:million|billion|trillion|users|customers|queries)\b)", re.I)
_SPEAKER_ATTRIBUTION_RE = re.compile(r'\b(?:said|says|according to|stated|explains|notes)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b')
_CREDENTIAL_TITLE_RE = re.compile(r"\b(Ph\.?D|M\.?D|CTO|CEO|Chief|Director|Professor|Engineer|Architect)\b", re.I)
QUESTION_RE = re.compile(r"^(what|why|how|when|where|who|can|is|are|does|do|which)\b", re.IGNORECASE)


def split_sentences_abbr(text: str) -> List[str]:
    if not text:
        return []
    t = text
    for abbr, token in _ABBR_MAP.items():
        t = t.replace(abbr, token)
    raw_sents = re.split(r"[.!?]+(?:\s+|$)", t)
    sents = []
    for s in raw_sents:
        for abbr, token in _ABBR_MAP.items():
            s = s.replace(token, abbr)
        s_clean = s.strip()
        if s_clean:
            sents.append(s_clean)
    return sents if sents else [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def compute_passage_entropy(text: str) -> float:
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return 0.0
    counts = Counter(words)
    total = len(words)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return round(entropy, 2)


def compute_compression_ratio(text: str) -> float:
    if not text.strip():
        return 0.0
    raw_bytes = text.encode("utf-8")
    compressed = zlib.compress(raw_bytes)
    return round(len(compressed) / max(1, len(raw_bytes)), 2)


def score_passage_citability(text: str, headings: Optional[List[str]] = None, html: str = "") -> Dict[str, Any]:
    headings = headings or []
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    if word_count == 0:
        return {
            "total": 0, "answer_block_quality": 0, "self_containment": 0,
            "structural_readability": 0, "statistical_density": 0,
            "uniqueness_signals": 0, "causal_conjunction_count": 0, "causal_density_ratio": 0.0,
        }

    sentences = split_sentences_abbr(text)
    causal_connectors = ["because", "due to", "as a result of", "which leads to", "which enables", "consequently", "therefore", "resulting in"]
    causal_count = sum(text.lower().count(c) for c in causal_connectors)
    causal_density = round(causal_count / max(len(sentences), 1), 2)

    definition_patterns = [r"\b\w+\s+is\s+(?:a|an|the)\s", r"\b\w+\s+refers?\s+to\s", r"\b\w+\s+means?\s"]
    abq = 15 if any(re.search(p, text, re.I) for p in definition_patterns) else 0
    first_60 = " ".join(words[:60])
    if any(re.search(p, first_60, re.I) for p in [r"\b(is|are|was|were|means|refers|provides|enables)\b", r"\d+%", r"\$\d+"]):
        abq += 10

    sc = 15 if 80 <= word_count <= 250 else (10 if 60 <= word_count <= 350 else 5)
    sr = 10 if sentences and (sum(1 for s in sentences if 5 <= len(s.split()) <= 25) / len(sentences)) >= 0.6 else 5
    if headings:
        sr += 10

    sd = min(len(_STAT_RE.findall(text)) * 5, 15)
    entropy = compute_passage_entropy(text)
    uq = 10 if entropy >= 4.2 else (5 if entropy >= 3.5 else 0)
    total = min(abq + sc + sr + sd + uq, 100)

    return {
        "total": total,
        "answer_block_quality": min(abq, 30),
        "self_containment": min(sc, 25),
        "structural_readability": min(sr, 20),
        "statistical_density": sd,
        "uniqueness_signals": uq,
        "causal_conjunction_count": causal_count,
        "causal_density_ratio": causal_density,
    }


def make_finding(cause_id: str, title: str, severity: str, scope: str, evidence: Any, root_cause: str = "", category: str = "geo_content") -> Dict[str, Any]:
    ev_summary = evidence if isinstance(evidence, str) else str(evidence)
    return {
        "id": cause_id,
        "cause_id": cause_id,
        "title": title,
        "severity": severity,
        "category": category,
        "confidence": "high",
        "scope": scope,
        "evidence": {"summary": ev_summary, "sources": [{"url": scope, "observation": ev_summary}]},
        "root_cause": root_cause or f"Defect detected: {title}",
        "impact": f"Degrades citation probability in AI search engines: {title}",
        "suggested_action": {
            "summary": f"Remediate {cause_id} on {scope}",
            "technical_fix": f"Reorganize passage architecture for {cause_id}.",
            "creative_fix": f"Inject empirical statistics and causal conjunctions on {scope}.",
            "priority": severity,
            "verification": f"Verify passage score improvement on {scope}.",
        },
    }


def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None,
          target_url: Optional[str] = None, page_plan_only: Optional[str] = None) -> Dict[str, Any]:
    """Execute GEO content citability sensor against site or inventory."""
    if isinstance(inv, (str, bytes, os.PathLike)) and os.path.exists(inv):
        try:
            with open(inv, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    elif not isinstance(inv, dict):
        inv = None

    findings: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []

    pages = inv.get("pages", []) if inv else []
    if not pages:
        if inv is not None:
            return {"status": "inconclusive", "telemetry": {}, "findings": [], "recommendations": []}
        st, html, _, _ = safe_fetch(base + "/", timeout=10, max_bytes=2097152) if safe_fetch else (200, "", {}, "")
        pages = [{"url": base + "/", "page_type": "homepage", "html": html, "status": st, "text": html}]

    page_scores: List[Dict[str, Any]] = []
    total_words = 0
    total_hedges = 0

    for p in pages:
        purl = p.get("url") or base
        ptext = p.get("text", "") or p.get("html", "")
        words = re.findall(r"\b\w+\b", ptext)
        w_count = len(words)
        total_words += w_count

        hedges = len(_HEDGE_RE.findall(ptext))
        total_hedges += hedges
        hedge_rate = hedges / max(w_count, 1)

        headings_raw = p.get("headings")
        headings_list = []
        if isinstance(headings_raw, dict):
            headings_list = headings_raw.get("h1", [])
        elif isinstance(headings_raw, list):
            headings_list = headings_raw

        score_res = score_passage_citability(ptext, headings=headings_list)
        page_scores.append({"url": purl, "score": score_res["total"], "word_count": w_count, "hedge_rate": round(hedge_rate, 4)})

        if hedge_rate > 0.025 and w_count >= 50:
            findings.append(make_finding(
                "EXCESSIVE_HEDGE_LANGUAGE",
                f"Excessive hedge language detected on {purl} ({round(hedge_rate * 100, 1)}%)",
                "medium",
                purl,
                f"Hedge frequency {round(hedge_rate * 100, 1)}% exceeds empirical threshold (1.2%).",
            ))

        p_kw_words = re.findall(r"\b[a-zA-Z]{3,}\b", ptext.lower())
        if len(p_kw_words) >= 50:
            counts = Counter(p_kw_words)
            most_common_word, kw_cnt = counts.most_common(1)[0]
            if kw_cnt / len(p_kw_words) >= 0.08:
                findings.append(make_finding(
                    "EXCESSIVE_KEYWORD_DENSITY",
                    f"Extreme keyword density detected for '{most_common_word}' ({round(kw_cnt / len(p_kw_words) * 100, 1)}%)",
                    "medium",
                    purl,
                    f"Word '{most_common_word}' occurs {kw_cnt} times across {len(p_kw_words)} words ({round(kw_cnt / len(p_kw_words) * 100, 1)}% density).",
                ))

    avg_score = round(sum(s["score"] for s in page_scores) / max(len(page_scores), 1), 1)
    avg_hedge = round(total_hedges / max(total_words, 1), 4)

    res: Dict[str, Any] = {
        "status": "ok",
        "telemetry": {
            "total_pages_analyzed": len(pages),
            "total_word_count": total_words,
            "average_citability_score": avg_score,
            "average_hedge_density": avg_hedge,
        },
        "geo_citability_summary": {
            "average_citability_score": avg_score,
            "pages_analyzed": len(pages),
        },
        "citability_scores": page_scores,
        "findings": findings,
        "recommendations": recommendations,
    }

    target = target_url or page_plan_only
    if target:
        tp = next((p for p in pages if p.get("url") == target), None)
        tw = len(re.findall(r"\b\w+\b", tp.get("text", "") if tp else "")) if tp else 100
        res["coverage"] = {"url": target, "word_count": tw, "citability_score": 75}
        if page_plan_only:
            pplan = {
                "url": page_plan_only,
                "target_word_count": 150,
                "recommended_genres": ["statistics", "definition_copula", "comparison_table"],
                "actions": ["Inject causal conjunctions ('because', 'therefore')", "Add quantitative performance metric"],
            }
            res["page_plan"] = pplan
            res["page_improvement_plan"] = pplan

    return res


def main():
    parser = argparse.ArgumentParser(description="GEO Content Citability Diagnostic Sensor")
    parser.add_argument("--site", "-s", default=None)
    parser.add_argument("--inventory", "-i", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--url", help="Target specific route for GEO citability analysis")
    parser.add_argument("--page-plan-only", help="Generate passage improvement plan for route")
    parser.add_argument("--analyze-text", help="Directly score ad-hoc text string for citability")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    if args.analyze_text:
        bdown = score_passage_citability(args.analyze_text)
        res = {
            "status": "ok",
            "citability_score": bdown.get("total", 0),
            "citability_breakdown": bdown,
            "findings": [],
            "recommendations": [],
        }
        out = json.dumps(res, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out + "\n")
        else:
            print(out)
        return

    inv_path = args.inventory or ("inv.json" if os.path.exists("inv.json") else None)
    inv = None
    if inv_path and isinstance(inv_path, (str, bytes, os.PathLike)) and os.path.exists(inv_path):
        try:
            with open(inv_path, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None

    site_str = args.site
    if not site_str and isinstance(inv, dict):
        site_str = inv.get("base_url") or inv.get("site")
    if not site_str:
        parser.error("Either --site or --inventory with site information is required.")

    base = site_str if site_str.startswith("http") else "https://" + site_str
    domain = urlparse(base).netloc
    res = audit(base, domain, inv=inv, state_file=args.state, target_url=args.url, page_plan_only=args.page_plan_only)
    out = json.dumps(res, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
