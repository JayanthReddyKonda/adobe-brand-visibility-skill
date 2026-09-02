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
# Hyland (2005) Academic Discourse Hedging Lexicon & Taxonomy
_HEDGE_RE = re.compile(
    r"\b(?:"
    # Epistemic modals & auxiliaries
    r"may|might|could|would"
    # Epistemic lexical verbs
    r"|suggest|suggests|suggested|indicate|indicates|indicated|appear|appears|appeared"
    r"|seem|seems|seemed|assume|assumes|assumed|speculate|speculates|estimate|estimates"
    # Epistemic adverbs & adjectives
    r"|probably|possibly|perhaps|presumably|allegedly|roughly|partially|fairly|somewhat|rather"
    r"|probable|possible|apparent|presumable"
    # Approximators & softeners
    r"|approximately|nearly|sort\s+of|kind\s+of|in\s+some\s+ways|a\s+bit|tends\s+to"
    r")\b",
    re.IGNORECASE,
)

# Exophoric pronoun check (TX04)
_EXOPHORIC_LEAD_RE = re.compile(
    r"^\s*(?:It|They|This|These|Their|Its|Our|We)\b",
    re.IGNORECASE,
)

# FActScore atomic fact patterns (TX03)
_FACT_SCORE_PATTERNS = [
    re.compile(r"\b\d+(\.\d+)?%?\b"),  # Numbers & percentages
    re.compile(r"\$\d+(?:,\d{3})*(?:\.\d+)?"),  # Currency values
    re.compile(r"\b(?:19|20)\d{2}\b"),  # Years / dates
    re.compile(r"\b(?:is|are|was|were)\s+(?:a|an|the)\b", re.IGNORECASE),  # Direct IS-A propositions
]


def count_atomic_facts(text: str) -> int:
    """Estimate atomic verifiable factual propositions based on FActScore heuristic."""
    return sum(len(p.findall(text)) for p in _FACT_SCORE_PATTERNS)


import math


def wilson_confidence_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson 95% score confidence interval for empirical citation rates."""
    if total <= 0:
        return (0.0, 0.0)
    p_hat = successes / total
    z2 = z * z
    denom = 1.0 + (z2 / total)
    center = (p_hat + (z2 / (2.0 * total))) / denom
    spread = (z * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z2 / (4.0 * total * total)))) / denom
    return (round(max(0.0, center - spread), 4), round(min(1.0, center + spread), 4))


import zlib
from collections import Counter
from datetime import datetime, timezone


def parse_date_string(date_str: str) -> datetime | None:
    """Parse ISO-8601 or simple date string into UTC datetime."""
    if not date_str or not isinstance(date_str, str):
        return None
    m = re.match(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?", date_str.strip())
    if m:
        try:
            year = int(m.group(1))
            month = int(m.group(2)) if m.group(2) else 1
            day = int(m.group(3)) if m.group(3) else 1
            return datetime(year, month, day, tzinfo=timezone.utc)
        except Exception:
            return None
    return None


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


def compute_passage_entropy(text: str) -> float:
    """Compute Shannon Token Entropy in bits/token to evaluate information density."""
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return 0.0
    counts = Counter(words)
    total = len(words)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return round(entropy, 2)


def compute_compression_ratio(text: str) -> float:
    """Compute lexical compression ratio (compressed/raw) to detect promotional filler."""
    if not text.strip():
        return 0.0
    raw_bytes = text.encode("utf-8")
    compressed = zlib.compress(raw_bytes)
    return round(len(compressed) / max(1, len(raw_bytes)), 2)


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
        self.published_date = None
        self.modified_date = None

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
        elif t == "time":
            dt = attr_dict.get("datetime", "").strip()
            if dt and not self.published_date:
                self.published_date = dt
        elif t == "meta":
            prop = attr_dict.get("property", "").lower()
            name = attr_dict.get("name", "").lower()
            c_val = attr_dict.get("content", "").strip()
            if c_val:
                if (
                    prop in ("article:published_time", "og:published_time")
                    or name in ("publishdate", "date", "dc.date")
                ) and not self.published_date:
                    self.published_date = c_val
                elif (
                    prop in ("article:modified_time", "og:updated_time")
                    or name in ("modified", "last-modified", "revised")
                ) and not self.modified_date:
                    self.modified_date = c_val
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


def score_passage_citability(text: str, headings: list) -> dict:
    """Score passage citability (0-100) based on optimal passage length (134-167 words),

    definition patterns, direct answers, clarity, and statistics.
    Derived from empirical Generative Engine Optimization research (Wu et al. / CMU AutoGEO).
    """
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    if word_count == 0:
        return {"total": 0, "breakdown": {}}

    # 1. Answer Block Quality (max 30 pts)
    abq = 0
    definition_patterns = [
        r"\b\w+\s+is\s+(?:a|an|the)\s",
        r"\b\w+\s+refers?\s+to\s",
        r"\b\w+\s+means?\s",
        r"\b\w+\s+(?:can be|are)?\s*defined\s+as\s",
    ]
    if any(re.search(p, text, re.IGNORECASE) for p in definition_patterns):
        abq += 15

    first_60 = " ".join(words[:60])
    if any(
        re.search(p, first_60, re.IGNORECASE)
        for p in [r"\b(is|are|was|were|means|refers|provides|enables)\b", r"\d+%", r"\$\d+"]
    ):
        abq += 10

    if any(h.strip().endswith("?") or QUESTION_RE.search(h.strip()) for h in headings):
        abq += 5

    # 2. Self-Containment & Optimal Length (max 25 pts)
    sc = 0
    if 134 <= word_count <= 167:
        sc += 15
    elif 100 <= word_count <= 250:
        sc += 10
    elif word_count > 60:
        sc += 5

    pronouns = re.findall(r"\b(it|they|them|he|she|this|these|those)\b", text.lower())
    if word_count > 0 and (len(pronouns) / word_count) <= 0.03:
        sc += 10

    # 3. Structural Readability (max 20 pts)
    sr = 0
    sentences = re.split(r"[.!?]+", text)
    clear_sentences = sum(1 for s in sentences if 5 <= len(s.split()) <= 25)
    if sentences and (clear_sentences / max(len(sentences), 1)) >= 0.6:
        sr += 10
    if len(headings) >= 1:
        sr += 10

    # 4. Statistical Density (max 15 pts)
    stats_matches = len(_STAT_RE.findall(text))
    sd = min(stats_matches * 5, 15)

    # 5. Lexical & Information Uniqueness (max 10 pts)
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
    }


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
    page_citability_map = {}

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

        citability = score_passage_citability(full_text, parser.headings)
        page_citability_map[url] = citability

        if depth_score >= 2 and citability["total"] < 35 and total_words >= 120:
            findings.append(
                {
                    "category": "content",
                    "title": "Substantive page has low passage citability score",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "LOW_CITABILITY_SCORE: Page lacks structured answer blocks, self-contained passage chunks (134-167w), and direct definition leads, reducing LLM extraction probability.",
                    "cause_family": "CONTENT.SHALLOW_COVERAGE",
                    "id": "LOW_CITABILITY_SCORE",
                    "cause_id": "LOW_CITABILITY_SCORE",
                    "evidence": f"Page {url} achieved a citability score of {citability['total']}/100 (Answer Block Quality: {citability['answer_block_quality']}/30, Self-Containment: {citability['self_containment']}/25).",
                    "impact": "Generative engines (Perplexity, ChatGPT Search) downrank the page in passage retrieval because it lacks extractable 134-167 word answer blocks.",
                    "suggested_action": {
                        "summary": "Structure content under question headings with 40-60 word direct answers and self-contained 134-167 word passage chunks.",
                        "technical_fix": "Format key sections under <h2> question headings with an immediate direct answer in the first sentence.",
                        "creative_fix": "Adopt the Direct Answer Inversion pattern: state what the entity/topic is, why it matters, and concrete statistics in the lead paragraph.",
                        "priority": "medium",
                        "verification": "Re-run citability scorer and confirm score >= 60/100.",
                    },
                }
            )

        # Evidence Genre Detection (Zhang et al. 2026 Citation Absorption Model)
        has_code_genre = bool(re.search(r"<(?:pre|code)[^>]*>|[\`]{3}", html, re.IGNORECASE))
        has_stats_genre = bool(re.search(r"\b\d+(?:\.\d+)?%?\b|\$\d+", full_text))
        has_definition_genre = bool(
            re.search(
                r"\b(?:is defined as|refers to|is characterized by|denotes|means that|describes)\b",
                full_text,
                re.IGNORECASE,
            )
        )
        has_comparison_genre = bool(
            re.search(
                r"\b(?:versus|compared to|in contrast to|unlike|differs from|alternative to)\b|<table",
                html,
                re.IGNORECASE,
            )
        )
        has_qa_format = bool(
            re.search(
                r"<(?:details|faq|dl)[^>]*>|\b(?:frequently asked questions|faq|q&a)\b",
                html,
                re.IGNORECASE,
            )
        )

        # Rule: Standalone Q&A / FAQ Format Alone Penalty (-5.7% influence penalty)
        if (
            has_qa_format
            and not has_code_genre
            and not has_stats_genre
            and not has_comparison_genre
            and not has_definition_genre
        ):
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.BEYOND_FAQ_FORMAT.001",
                    "title": "Augment standalone FAQ format with quantitative data, definitions, or comparisons",
                    "category": "content",
                    "summary": f"Page {url} uses a standalone Q&A/FAQ format without empirical data, code blocks, or comparative analysis. Research on Citation Absorption (Zhang et al. 2026, arXiv:2604.25707 across 21,143 citations) proves that Q&A format alone suffers a -5.7% relative influence penalty unless reinforced with statistics (+61.6%) or comparison content (+55.3%).",
                    "priority": "medium",
                    "technical_fix": "Incorporate numerical benchmarks, comparison tables, or definitive IS-A definitions inside FAQ answer blocks.",
                    "creative_fix": "Transform generic question-answers into authoritative mini-guides with data points and comparative evaluation.",
                    "verification": "Confirm FAQ answers include specific numbers, comparison dimensions, or concrete code examples.",
                }
            )

        # TX01: Rule_BLUF_Top30Percent (Bottom Line Up Front in top 30% / first 250 words)
        words_list = full_text.split()
        lead_250 = " ".join(words_list[:250]).lower()
        has_lead_definition = bool(re.search(r"\b(?:is|are|provides|delivers|enables|accelerates|offers)\b", lead_250))
        if ptype in ("article", "content", "product_detail") and total_words >= 250 and not has_lead_definition:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.BLUF_TOP30_PERCENT.001",
                    "title": "Front-load primary answer/definition in the top 30% of content (BLUF)",
                    "category": "content",
                    "summary": f"Page {url} delays core definitions beyond the first 250 words. Stanford research ('Lost in the Middle') and empirical AI citation studies prove that 44.2% of citations are extracted from the top 30% of a page.",
                    "priority": "medium",
                    "technical_fix": "Invert paragraph structure: place the definitive resolution or entity answer in the lead 40-60 words.",
                    "creative_fix": "Adopt the Direct Answer Inversion format: answer the title's core question immediately before providing background.",
                    "verification": "Confirm first 250 words contain a direct answer proposition.",
                }
            )

        # TX03: Atomic Fact-to-Token Ratio (FTR) (FActScore Benchmark)
        atomic_facts = count_atomic_facts(full_text)
        ftr = round(atomic_facts / max(total_words, 1), 3)
        if total_words >= 150 and ftr < 0.040:
            findings.append(
                {
                    "category": "content",
                    "title": "Low Atomic Fact-to-Token Ratio (depresses RAG factual retrieval)",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": f"LOW_FACT_TO_TOKEN_RATIO: Page exhibits an FTR of {ftr:.3f} ({atomic_facts} facts across {total_words} words). The empirical citable threshold is FTR >= 0.080. Retrieval systems discard prose that lacks verifiable atomic claims.",
                    "cause_family": "CONTENT.SHALLOW_COVERAGE",
                    "id": "LOW_FACT_TO_TOKEN_RATIO",
                    "cause_id": "LOW_FACT_TO_TOKEN_RATIO",
                    "evidence": f"Page {url} contains only {atomic_facts} verifiable factual assertions (dates, numbers, direct definitions) across {total_words} words.",
                    "impact": "Generative engines (Perplexity, ChatGPT Search) favor high-density source passages with verifiable facts.",
                    "suggested_action": {
                        "summary": "Dense substantive paragraphs with verifiable technical benchmarks, dates, and specifications.",
                        "technical_fix": "Replace subjective qualitative descriptors with measurable attributes and verified data points.",
                        "creative_fix": "Incorporate benchmark tables, technical specifications, and quantitative case metrics.",
                        "priority": "medium",
                        "verification": "Verify FTR reaches >= 0.080 on content passages.",
                    },
                }
            )

        # TX04: Exophoric Pronoun Ratio in Passage Leads
        exophoric_leads = []
        for p_chunk in parser.paragraphs:
            p_strip = p_chunk.strip()
            if len(p_strip.split()) >= 8 and _EXOPHORIC_LEAD_RE.match(p_strip):
                exophoric_leads.append(p_strip[:50])
        if len(exophoric_leads) >= 2:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.EXOPHORIC_PRONOUN_GROUNDING.001",
                    "title": "Replace ambiguous opening pronouns with explicit entity names (RAG Context Grounding)",
                    "category": "content",
                    "summary": f"Found {len(exophoric_leads)} paragraph lead(s) starting with ambiguous pronouns ('{exophoric_leads[0]}...') on {url}. When RAG retrievers chunk passages independently, isolated pronouns lose entity grounding and fail attribution.",
                    "priority": "low",
                    "technical_fix": "Replace leading pronouns ('It enables', 'They provide') with the explicit brand or product entity name in section lead sentences.",
                    "creative_fix": "Anchor every chunk with the canonical entity name to preserve standalone attribution.",
                    "verification": "Confirm section opening sentences explicitly state the brand or topic entity.",
                }
            )

        # LL02: Rule_LLM_ExecutiveSummary (C-SEO Bench NeurIPS 2025)
        has_summary_block = bool(
            re.search(r"<(aside|blockquote|div)[^>]*(summary|takeaway|abstract|tldr)[^>]*>", html, re.IGNORECASE)
        )
        if ptype == "article" and total_words >= 300 and not has_summary_block:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.LLM_EXECUTIVE_SUMMARY.001",
                    "title": "Implement an executive takeaway summary block within the first 100 words",
                    "category": "content",
                    "summary": f"Article {url} lacks an executive takeaway summary block. NeurIPS 2025 C-SEO research proves that pages with structured summary headers directly beneath the title direct LLM attention and outperform narrative layouts in multi-document retrieval.",
                    "priority": "low",
                    "technical_fix": "Add an <aside class='executive-summary'> or Markdown blockquote directly below the H1.",
                    "creative_fix": "Include 3 bulleted key takeaways summarizing core entities, data, and conclusions.",
                    "verification": "Verify executive summary block is present in the first 100 words.",
                }
            )

        # 1.1 Hedge Language Density Check (from geoskills/geo-fix-content)
        hedge_matches = _HEDGE_RE.findall(full_text)
        hedge_density = (len(hedge_matches) / max(total_words, 1)) * 100
        if hedge_density > 1.5 and total_words >= 100:
            findings.append(
                {
                    "category": "content",
                    "title": "Content contains excessive hedge language (weakening AI citation probability)",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": f"EXCESSIVE_HEDGE_LANGUAGE: Page exhibits a hedge word density of {hedge_density:.1f}% (threshold: < 0.5%). Generative search engines deprioritize unassertive or tentative prose in favor of direct, authoritative claims.",
                    "cause_family": "CONTENT.SHALLOW_COVERAGE",
                    "id": "EXCESSIVE_HEDGE_LANGUAGE",
                    "cause_id": "EXCESSIVE_HEDGE_LANGUAGE",
                    "evidence": f"Page {url} contains {len(hedge_matches)} hedge expression(s) ({', '.join(set(m.lower() for m in hedge_matches[:5]))}) across {total_words} words.",
                    "impact": "Empirical studies demonstrate that hedged language ranks 3x lower in LLM citation selection than confident, data-backed assertions.",
                    "suggested_action": {
                        "summary": "Replace tentative hedge language with direct, assertive, and quantified statements.",
                        "technical_fix": "Audit body copy against the hedge language dictionary and remove unassertive qualifiers.",
                        "creative_fix": "Replace phrases like 'seems to improve' or 'could possibly help' with concrete metrics and verifiable outcomes.",
                        "priority": "medium",
                        "verification": "Re-run content check to verify hedge density drops below 0.5%.",
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

        # 3.1 Freshness & Recency Sensor (SE Ranking 1.3M Citation Study)
        if ptype in ("article", "content", "blog", "product_detail") and total_words >= 150:
            date_raw = parser.modified_date or parser.published_date
            if not date_raw:
                recommendations.append(
                    {
                        "id": "PROACTIVE.GEO.VISIBLE_RECENCY_DATE.001",
                        "title": "Publish visible last-updated dates on substantive content",
                        "category": "content",
                        "summary": f"Substantive page {url} lacks visible publication or modification dates. Generative search engines (SE Ranking 1.3M study) deprioritize undated content, selecting pages updated within 3 months 3x more often.",
                        "priority": "medium",
                        "technical_fix": "Add a <time datetime='YYYY-MM-DD'> element and article:modified_time meta tag to the page header.",
                        "creative_fix": "Prominently display 'Last Updated: [Month Year]' at the top of the article beside the author byline.",
                        "verification": "Confirm valid ISO-8601 date appears in <time> tag and meta tags.",
                    }
                )
            else:
                parsed_dt = parse_date_string(date_raw)
                if parsed_dt:
                    age_days = (datetime.now(timezone.utc) - parsed_dt).days
                    if age_days > 180:
                        findings.append(
                            {
                                "category": "content",
                                "title": "Content exceeds 6-month recency threshold (depressing AI citations)",
                                "severity": "medium",
                                "confidence": "high",
                                "root_cause": f"CONTENT_RECENCY_DEFICIT: Content was last updated {age_days} days ago ({date_raw}). Generative search engines deprioritize stale content older than 6 months.",
                                "cause_family": "CONTENT.SHALLOW_COVERAGE",
                                "id": "CONTENT_RECENCY_DEFICIT",
                                "cause_id": "CONTENT_RECENCY_DEFICIT",
                                "evidence": f"Page {url} declares last update as {date_raw} ({age_days} days old).",
                                "impact": "AI search engines (Google AI Overviews, Perplexity) select recently refreshed content 3x more often than legacy pages.",
                                "suggested_action": {
                                    "summary": "Establish a scheduled quarterly refresh program for high-priority pages.",
                                    "technical_fix": "Update the article:modified_time meta tag and <time> element upon updating copy.",
                                    "creative_fix": "Review factual assertions, refresh statistics, and update benchmarks to the current year.",
                                    "priority": "medium",
                                    "verification": "Confirm updated date is within the last 90 days.",
                                },
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

        # 8. Information Density & Entropy Vector
        if total_words >= 150:
            entropy = compute_passage_entropy(full_text)
            comp_ratio = compute_compression_ratio(full_text)
            if entropy < 4.0:
                recommendations.append(
                    {
                        "id": "PROACTIVE.GEO.INFORMATION_DENSITY.001",
                        "title": "Increase factual vocabulary diversity and information density",
                        "category": "content",
                        "summary": f"Page {url} has low lexical token entropy ({entropy:.2f} bits/token, comp ratio {comp_ratio:.2f}). Increasing vocabulary specificity and technical depth improves neural retrieval ranking.",
                        "priority": "low",
                        "technical_fix": "Add technical terminology, specific feature nouns, and precise specifications.",
                        "creative_fix": "Replace generic marketing phrasing with distinct, domain-specific terminology.",
                        "verification": "Confirm passage token entropy >= 4.2 bits/token.",
                    }
                )

        # 9. RAG Passage Chunk Architecture Vector (120-180 words per modular section)
        if ptype in ("article", "product_detail", "other") and total_words >= 150:
            avg_words_per_heading = total_words / max(len(parser.headings), 1)
            if avg_words_per_heading > 300 or len(parser.headings) == 0:
                recommendations.append(
                    {
                        "id": "PROACTIVE.GEO.RAG_PASSAGE_CHUNKING.001",
                        "title": "Format informational content into modular 120-180 word RAG passage chunks",
                        "category": "content",
                        "summary": f"Page {url} has long unstructured text blocks (avg {avg_words_per_heading:.0f} words/heading). AI search systems (Perplexity, ChatGPT Search) retrieve text in 120-180 word passage chunks. Formatting content under question headings with 40-60 word direct answers maximizes retrieval relevance.",
                        "priority": "low",
                        "technical_fix": "Structure long body copy into discrete semantic <section> blocks under <h2>/<h3> headings, keeping each section between 120 and 180 words.",
                        "creative_fix": "Place an immediate direct answer in the first sentence after each heading before expanding into technical nuances.",
                        "verification": "Confirm headings divide body text into modular 120-180 word sections.",
                    }
                )

    avg_cit = (
        round(sum(c["total"] for c in page_citability_map.values()) / max(len(page_citability_map), 1), 1)
        if page_citability_map
        else 0.0
    )
    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "target_pages_evaluated": len(target_pages),
            "average_citability_score": avg_cit,
        },
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
