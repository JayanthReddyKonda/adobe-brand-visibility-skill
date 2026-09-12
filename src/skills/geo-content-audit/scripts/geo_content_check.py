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
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore

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
_QUOTATION_RE = re.compile(r'["“]([^"”]{12,300})["”]', re.MULTILINE)
_SPEAKER_ATTRIBUTION_RE = re.compile(
    r"\b(?:said|says|stated|noted|according to|argues|explains|writes|reported by|explained by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    re.IGNORECASE,
)
_CREDENTIAL_TITLE_RE = re.compile(
    r"\b(?:Dr\.|PhD|MD|Professor|Prof\.|Chief Scientist|VP of|Director of|Lead Researcher|Principal Scientist)\b",
    re.IGNORECASE,
)
_ABBR_MAP = {
    "e.g.": "__ABBR_EG__",
    "i.e.": "__ABBR_IE__",
    "Dr.": "__ABBR_DR__",
    "Prof.": "__ABBR_PROF__",
    "Mr.": "__ABBR_MR__",
    "Ms.": "__ABBR_MS__",
    "Mrs.": "__ABBR_MRS__",
    "Ph.D.": "__ABBR_PHD__",
    "vs.": "__ABBR_VS__",
    "Inc.": "__ABBR_INC__",
    "Ltd.": "__ABBR_LTD__",
}


def split_sentences_abbr(text: str) -> list:
    """Split sentences protecting common abbreviations with periods."""
    if not text:
        return []
    t = text
    for abbr, token in _ABBR_MAP.items():
        if abbr in t:
            t = t.replace(abbr, token)
    raw_sents = re.split(r"[.!?]+(?:\s+|$)", t)
    sents = []
    for s in raw_sents:
        for abbr, token in _ABBR_MAP.items():
            if token in s:
                s = s.replace(token, abbr)
        s_clean = s.strip()
        if s_clean:
            sents.append(s_clean)
    return sents if sents else [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


_COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're",
    "you've", "your", "yours", "yourself", "yourselves",
}
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

# Atomic Fact Density Heuristic (AFDH) patterns (TX03)
_AFDH_PATTERNS = [
    re.compile(r"\b\d+(\.\d+)?%?\b"),  # Numbers & percentages
    re.compile(r"\$\d+(?:,\d{3})*(?:\.\d+)?"),  # Currency values
    re.compile(r"\b(?:19|20)\d{2}\b"),  # Years / dates
    re.compile(r"\b(?:is|are|was|were)\s+(?:a|an|the)\b", re.IGNORECASE),  # Direct IS-A propositions
]


def count_atomic_facts(text: str) -> int:
    """Estimate atomic verifiable factual propositions based on Atomic Fact Density Heuristic (AFDH)."""
    return sum(len(p.findall(text)) for p in _AFDH_PATTERNS)


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


def extract_attributed_quotations(html: str, full_text: str) -> dict:
    """Extract and analyze attributed quotations (Princeton KDD 2024: +40.9% PAWC lift).

    Verifies whether quotes are tied to named speakers or credentials rather than raw punctuation marks.
    """
    quotes = _QUOTATION_RE.findall(full_text)
    has_blockquote = bool(re.search(r"<(?:blockquote|q)\b[^>]*>", html, re.IGNORECASE))

    speakers = _SPEAKER_ATTRIBUTION_RE.findall(full_text)
    has_credentials = bool(_CREDENTIAL_TITLE_RE.search(full_text))

    attributed_count = 0
    if speakers or (quotes and has_credentials) or (has_blockquote and has_credentials):
        attributed_count = max(len(speakers), 1 if (quotes and has_credentials) else 0)

    return {
        "total_quotes": len(quotes) + (1 if has_blockquote else 0),
        "attributed_quotes": attributed_count,
        "has_named_expert": bool(speakers or has_credentials),
        "speakers_identified": list(set(speakers[:5])),
    }


def analyze_evidence_genres(html: str, full_text: str, parser) -> dict:
    """Analyze the 5 high-influence evidence genres based on Zhang et al. 2026 (arXiv:2604.25707):
    - Code (+76.9%)
    - Statistics (+61.6%)
    - Definition Copula (+57.3%)
    - Comparison Table (+55.3%)
    - Procedural Steps (+41.2%)
    Also evaluates Standalone FAQ Deficit (-5.7% citation penalty).
    """
    genres = []
    details = {}

    has_code = getattr(parser, "code_blocks", 0) > 0 or bool(re.search(r"<(?:pre|code)\b|```", html, re.IGNORECASE))
    if has_code:
        genres.append("code")
    details["has_code"] = has_code

    stat_matches = len(_STAT_RE.findall(full_text))
    has_stats = stat_matches >= 1
    if has_stats:
        genres.append("statistics")
    details["statistics_count"] = stat_matches

    has_definition = bool(
        re.search(
            r"\b(?:\w+\s+is\s+(?:a|an|the)|is defined as|refers to|is characterized by|denotes|means that)\b",
            full_text,
            re.IGNORECASE,
        )
    )
    if has_definition:
        genres.append("definition_copula")
    details["has_definition"] = has_definition

    has_table = getattr(parser, "tables", 0) > 0 or bool(
        re.search(r"<table\b|\b(?:versus|compared to|in contrast to|unlike|differs from)\b", html, re.IGNORECASE)
    )
    if has_table:
        genres.append("comparison_table")
    details["has_comparison_table"] = has_table

    has_steps = getattr(parser, "ordered_lists", 0) > 0 or bool(
        re.search(r"<ol\b|\b(?:step\s+\d+|1\.\s+[A-Z])\b", html, re.IGNORECASE)
    )
    if has_steps:
        genres.append("procedural_steps")
    details["has_procedural_steps"] = has_steps

    has_qa_format = bool(
        re.search(
            r"<(?:details|faq|dl)\b[^>]*>|\b(?:frequently asked questions|faq|q&a)\b",
            html,
            re.IGNORECASE,
        )
    ) or any(h.strip().endswith("?") or QUESTION_RE.search(h.strip()) for h in getattr(parser, "headings", []))

    standalone_faq_deficit = has_qa_format and len(genres) < 2

    return {
        "genres_detected": genres,
        "genre_count": len(genres),
        "standalone_faq_deficit": standalone_faq_deficit,
        "has_qa_format": has_qa_format,
        "details": details,
    }


def detect_keyword_stuffing(full_text: str) -> dict:
    """Detect keyword stuffing and token over-concentration (-8.3% to -10% citation degradation in LLMs).
    Evaluates non-stopword token frequencies. A density > 4.5% triggers degradation penalty.
    """
    words = re.findall(r"\b[a-zA-Z]{3,}\b", full_text.lower())
    if len(words) < 150:
        return {"is_stuffed": False, "max_density": 0.0, "top_repeated_words": []}

    content_words = [w for w in words if w not in _COMMON_STOPWORDS]
    if not content_words:
        return {"is_stuffed": False, "max_density": 0.0, "top_repeated_words": []}

    counts = Counter(content_words)
    total_words = len(words)
    top_items = []
    max_density = 0.0

    for word, count in counts.most_common(5):
        density = count / total_words
        top_items.append((word, round(density, 4)))
        if density > max_density:
            max_density = density

    is_stuffed = max_density > 0.045
    return {
        "is_stuffed": is_stuffed,
        "max_density": round(max_density, 4),
        "top_repeated_words": top_items,
    }


def analyze_bluf_placement(full_text: str, total_words: int) -> dict:
    """Analyze Bottom Line Up Front (BLUF) answer placement (Liu et al. Stanford 'Lost in the Middle').
    Generative engines exhibit strong positional bias favoring the beginning of document context (top 30% / first 250 words).
    """
    words_list = full_text.split()
    if not words_list:
        return {"bluf_present_in_top30": False, "first_answer_position_pct": 1.0, "lead_word_count": 0}

    top_30_cutoff = min(250, max(60, int(len(words_list) * 0.30)))
    lead_text = " ".join(words_list[:top_30_cutoff])

    definition_lead_re = re.compile(
        r"\b(?:is|are|provides|delivers|enables|accelerates|offers|means|defined as|refers to)\b",
        re.IGNORECASE,
    )
    has_lead_answer = bool(definition_lead_re.search(lead_text))

    return {
        "bluf_present_in_top30": has_lead_answer,
        "lead_word_count": top_30_cutoff,
        "first_answer_position_pct": 0.15 if has_lead_answer else 0.65,
    }


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
        self.code_blocks = 0
        self.blockquotes = 0
        self.ordered_lists = 0
        self.published_date = None
        self.modified_date = None

    @property
    def extracted_text(self):
        return " ".join(self.text_blocks)

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()
        self.current_tag = t

        if t in ("script", "style"):
            self.in_script = True
        elif t == "table":
            self.tables += 1
        elif t in ("ul", "dl"):
            self.lists += 1
        elif t == "ol":
            self.ordered_lists += 1
            self.lists += 1
        elif t in ("pre", "code"):
            self.code_blocks += 1
        elif t == "blockquote":
            self.blockquotes += 1
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


def score_passage_citability(text: str, headings: list, html: str = "") -> dict:
    """Score passage citability (0-100) based on optimal passage length (134-167 words),

    definition patterns, direct answers, clarity, and statistics.
    Derived from empirical Generative Engine Optimization research (Wu et al. / CMU AutoGEO).
    """
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    if word_count == 0:
        return {
            "total": 0,
            "answer_block_quality": 0,
            "self_containment": 0,
            "structural_readability": 0,
            "statistical_density": 0,
            "uniqueness_signals": 0,
            "evidence_genres_score": 0,
            "attributed_quotations_score": 0,
            "bluf_primacy_score": 0,
            "breakdown": {},
        }

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
    if 80 <= word_count <= 250:
        sc += 15
    elif 60 <= word_count <= 350:
        sc += 10
    elif word_count > 40:
        sc += 5

    pronouns = re.findall(r"\b(it|they|them|he|she|this|these|those)\b", text.lower())
    if word_count > 0 and (len(pronouns) / word_count) <= 0.03:
        sc += 10

    # 3. Structural Readability (max 20 pts)
    sr = 0
    sentences = split_sentences_abbr(text)
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

    # 6. Deep GEO Empirical Sub-dimensions (Zhang et al. 2026, Princeton KDD 2024)
    evidence_score = 0
    if stats_matches > 0:
        evidence_score += 4
    if any(re.search(p, text, re.IGNORECASE) for p in definition_patterns):
        evidence_score += 4
    if html and ("<table" in html.lower() or "versus" in text.lower()):
        evidence_score += 4
    if html and ("<pre" in html.lower() or "<code" in html.lower() or "```" in text):
        evidence_score += 4
    if html and ("<ol" in html.lower() or "step 1" in text.lower()):
        evidence_score += 4

    quotes_score = (
        10
        if (_SPEAKER_ATTRIBUTION_RE.search(text) or _CREDENTIAL_TITLE_RE.search(text))
        else (5 if ('"' in text or "“" in text) else 0)
    )
    bluf_score = (
        10
        if any(
            re.search(p, first_60, re.IGNORECASE)
            for p in [r"\b(is|are|was|were|means|refers|provides|enables)\b"]
        )
        else 0
    )

    causal_connectors = [
        "because",
        "due to",
        "as a result of",
        "which leads to",
        "which enables",
        "consequently",
        "therefore",
        "resulting in",
    ]
    causal_count = sum(text.lower().count(c) for c in causal_connectors)
    causal_density = round(causal_count / max(len(sentences), 1), 2)

    total = min(abq + sc + sr + sd + uq, 100)
    return {
        "total": total,
        "answer_block_quality": min(abq, 30),
        "self_containment": min(sc, 25),
        "structural_readability": min(sr, 20),
        "statistical_density": sd,
        "uniqueness_signals": uq,
        "evidence_genres_score": min(evidence_score, 20),
        "attributed_quotations_score": quotes_score,
        "bluf_primacy_score": bluf_score,
        "causal_conjunction_count": causal_count,
        "causal_density_ratio": causal_density,
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

    target_pages = [
        p
        for p in html_pages
        if p.get("page_type")
        in ("product_detail", "product", "article", "pricing", "about", "documentation", "guide", "faq")
    ]
    if not target_pages:
        target_pages = html_pages
    page_citability_map = {}
    page_improvement_plans: list[dict] = []

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
        has_auth_citation = False
        has_credentials = False

        # Run deep empirical sensors
        attributed_quotes_data = extract_attributed_quotations(html, full_text)
        evidence_genre_data = analyze_evidence_genres(html, full_text, parser)
        kw_stuffing_data = detect_keyword_stuffing(full_text)
        bluf_data = analyze_bluf_placement(full_text, total_words)

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

        if depth_score < 2 and total_words >= 60:
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
                    "url": url,
                    "scope": url,
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

        citability = score_passage_citability(full_text, parser.headings, html=html)
        page_citability_map[url] = citability

        if depth_score >= 2 and citability["total"] < 35 and total_words >= 120:
            findings.append(
                {
                    "category": "content",
                    "title": "Substantive page has low passage citability score",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "LOW_CITABILITY_SCORE: Page lacks structured answer blocks, self-contained passage chunks (80-250 words), and direct definition leads, reducing LLM extraction probability.",
                    "cause_family": "CONTENT.SHALLOW_COVERAGE",
                    "id": "LOW_CITABILITY_SCORE",
                    "cause_id": "LOW_CITABILITY_SCORE",
                    "url": url,
                    "scope": url,
                    "evidence": f"Page {url} achieved a citability score of {citability['total']}/100 (Answer Block Quality: {citability['answer_block_quality']}/30, Self-Containment: {citability['self_containment']}/25).",
                    "impact": "Generative engines (Perplexity, ChatGPT Search) downrank the page in passage retrieval because it lacks extractable 80-250 word standalone answer blocks.",
                    "suggested_action": {
                        "summary": "Structure content under question headings with 40-60 word direct answers and self-contained 80-250 word passage chunks.",
                        "technical_fix": "Format key sections under <h2> question headings with an immediate direct answer in the first sentence.",
                        "creative_fix": "Adopt the Direct Answer Inversion pattern: state what the entity/topic is, why it matters, and concrete statistics in the lead paragraph.",
                        "priority": "medium",
                        "verification": "Re-run citability scorer and confirm score >= 60/100.",
                    },
                }
            )

        # Standalone Q&A / FAQ Format Alone Penalty (-5.7% citation penalty from Zhang et al. 2026)
        if evidence_genre_data["standalone_faq_deficit"]:
            findings.append(
                {
                    "category": "content",
                    "title": "Standalone FAQ format lacks supporting empirical evidence genres",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "STANDALONE_FAQ_DEFICIT: Page uses isolated Q&A/FAQ format without supporting empirical evidence (code, statistics, definition copulas, or comparison tables). Research shows standalone FAQ formats suffer an empirical -5.7% citation penalty.",
                    "cause_family": "CONTENT.STANDALONE_FAQ_DEFICIT",
                    "id": "STANDALONE_FAQ_DEFICIT",
                    "cause_id": "STANDALONE_FAQ_DEFICIT",
                    "url": url,
                    "scope": url,
                    "evidence": f"Page {url} utilizes FAQ/Q&A structure but contains only {evidence_genre_data['genre_count']} of the 5 high-influence evidence genres ({', '.join(evidence_genre_data['genres_detected']) or 'none'}).",
                    "impact": "LLM retrieval engines heavily discount unverified FAQ prose in favor of multi-dimensional evidence passages.",
                    "suggested_action": {
                        "summary": "Reinforce FAQ answers with concrete statistics, code snippets, or comparative tables.",
                        "technical_fix": "Add benchmark metrics, code examples, or comparison matrices directly into the FAQ answer blocks.",
                        "creative_fix": "Rewrite answers from conversational soundbites into substantive technical explanations with verifiable figures.",
                        "priority": "medium",
                        "verification": "Confirm at least 2 evidence genres are present within the page body.",
                    },
                }
            )
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

        # Keyword Stuffing Sensor (-8.3% to -10% citation degradation in LLMs)
        if kw_stuffing_data["is_stuffed"]:
            top_word, top_density = kw_stuffing_data["top_repeated_words"][0]
            findings.append(
                {
                    "category": "content",
                    "title": "Unnatural keyword concentration depresses neural citation retrieval",
                    "severity": "medium",
                    "confidence": "medium",
                    "root_cause": f"EXCESSIVE_KEYWORD_DENSITY: Term '{top_word}' occurs at {top_density * 100:.1f}% density (threshold: < 4.5%). Repetitive keyword targeting degrades neural embedding perplexity and incurs an empirical -8.3% to -10% citation penalty in modern LLM generative engines.",
                    "cause_family": "CONTENT.KEYWORD_STUFFING_DEGRADATION",
                    "id": "EXCESSIVE_KEYWORD_DENSITY",
                    "cause_id": "EXCESSIVE_KEYWORD_DENSITY",
                    "url": url,
                    "scope": url,
                    "evidence": f"Page {url} contains extreme term frequency for '{top_word}' ({top_density * 100:.1f}% of body tokens). Top repeated terms: {', '.join(f'{w} ({d * 100:.1f}%)' for w, d in kw_stuffing_data['top_repeated_words'][:3])}.",
                    "impact": "Generative retrieval models (Perplexity, ChatGPT Search, Claude) penalize keyword-stuffed passages during neural reranking.",
                    "suggested_action": {
                        "summary": "Diversify lexical vocabulary with domain synonyms, semantic co-occurrences, and natural phrasing.",
                        "technical_fix": "Audit body copy and reduce repetitive token occurrences until term density falls below 3.5%.",
                        "creative_fix": "Replace repetitive brand or keyword phrases with varied conceptual terms, semantic attributes, and contextual pronouns.",
                        "priority": "medium",
                        "verification": "Confirm maximum individual non-stopword density is under 4.0%.",
                    },
                }
            )

        # TX01: Rule_BLUF_Top30Percent (Bottom Line Up Front in top 30% / first 250 words)
        has_lead_definition = bluf_data["bluf_present_in_top30"]
        if ptype in ("article", "content", "product_detail") and total_words >= 250 and not has_lead_definition:
            findings.append(
                {
                    "category": "content",
                    "title": "Core answer proposition delayed beyond top 30% of document (Lost in the Middle)",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "CONTEXT_PLACEMENT_DEGRADATION: Primary definitional proposition or answer is delayed beyond the first 250 words / top 30% of content. Positional bias in RAG and neural retrieval ('Lost in the Middle', Liu et al.) degrades extraction recall when core propositions are buried in mid-document narrative.",
                    "cause_family": "CONTENT.CONTEXT_PLACEMENT_DEGRADATION",
                    "id": "CONTEXT_PLACEMENT_DEGRADATION",
                    "cause_id": "CONTEXT_PLACEMENT_DEGRADATION",
                    "url": url,
                    "scope": url,
                    "evidence": f"Page {url} ({total_words} words) does not state its definitive resolution or entity proposition within the top {bluf_data['lead_word_count']} words.",
                    "impact": "Generative search engines truncate or downweight answers buried deep within long narrative text blocks.",
                    "suggested_action": {
                        "summary": "Front-load the core answer and canonical proposition in the first 50-75 words immediately beneath the primary heading.",
                        "technical_fix": "Restructure page layout using the Inverted Pyramid pattern: answer H1 query in paragraph 1.",
                        "creative_fix": "Craft a crisp 40-60 word definitive BLUF summary paragraph before diving into secondary features.",
                        "priority": "medium",
                        "verification": "Confirm opening 200 words contain direct definition copulas or quantitative propositions.",
                    },
                }
            )
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.BLUF_TOP30_PERCENT.001",
                    "title": "Front-load primary answer/definition in the top 30% of content (BLUF)",
                    "category": "content",
                    "summary": f"Page {url} delays core definitions beyond the first 250 words. Positional attention decay in RAG systems ('Lost in the Middle') causes neural extractors to prioritize facts positioned in opening sections.",
                    "priority": "medium",
                    "technical_fix": "Invert paragraph structure: place the definitive resolution or entity answer in the lead 40-60 words.",
                    "creative_fix": "Adopt the Direct Answer Inversion format: answer the title's core question immediately before providing background.",
                    "verification": "Confirm first 250 words contain a direct answer proposition.",
                }
            )

        # Attributed Quotations Check (Princeton KDD 2024: +40.9% lift)
        if (
            ptype in ("article", "content", "product_detail")
            and total_words >= 150
            and attributed_quotes_data["attributed_quotes"] == 0
        ):
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.ATTRIBUTED_EXPERT_QUOTES.001",
                    "title": "Integrate attributed quotations from named domain experts (+40.9% GEO citation lift)",
                    "category": "content",
                    "summary": f"Page {url} lacks attributed quotations from named experts or recognized authorities. Princeton KDD 2024 empirical research demonstrated that incorporating Attributed Quotations yields the single highest citation lift (+40.9% PAWC boost) among all tested optimization vectors, outperforming raw statistical claims alone.",
                    "priority": "medium",
                    "technical_fix": "Incorporate <blockquote> elements with <cite> tags attributing direct insights to credentialed industry specialists or named leaders.",
                    "creative_fix": "Quote internal or external domain authorities with their title and organization (e.g., 'according to Dr. Jane Doe, Chief Scientist...').",
                    "verification": "Confirm quotation is explicitly attributed to a named individual with professional credentials.",
                }
            )

        # Author Attribution & Credential Check (Princeton KDD 2024 / E-E-A-T)
        has_author_signal = bool(p.get("authors")) or has_credentials or _CREDENTIAL_RE.search(full_text)
        if ptype in ("article", "guide", "documentation") and total_words >= 200 and not has_author_signal:
            recommendations.append(
                {
                    "id": "PROACTIVE.GEO.CREDENTIALED_AUTHOR_ATTRIBUTION.001",
                    "title": "Publish credentialed author bylines on informational assets",
                    "category": "content",
                    "summary": f"Page {url} lacks explicit author attribution or professional credentials. AI models heavily favor verifiable human expertise and credentialed bylines when selecting authoritative citation sources.",
                    "priority": "medium",
                    "technical_fix": "Add <meta name='author' content='...'> and Schema.org Author markup with Person credentials (e.g. jobTitle, worksFor).",
                    "creative_fix": "Include author bylines with relevant domain expertise, degrees, or industry experience in article headers.",
                    "verification": "Confirm page publishes visible author name and Schema.org Person markup.",
                }
            )

        # Commercial CTA Intrusion on Informational Routes
        if ptype in ("article", "documentation", "guide", "faq"):
            comm_ctas = [
                c for c in p.get("ctas", [])
                if (c.get("is_commercial_cta") if isinstance(c, dict) else getattr(c, "is_commercial_cta", False))
            ]
            if len(comm_ctas) >= 4:
                findings.append(
                    {
                        "category": "content",
                        "title": "Excessive commercial CTA intrusion inside informational content",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": f"COMMERCIAL_INTRUSION: Page contains {len(comm_ctas)} commercial call-to-action elements within informational prose, reducing factual authority scores.",
                        "cause_family": "CONTENT.SHALLOW_COVERAGE",
                        "id": "COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT",
                        "cause_id": "COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT",
                        "url": url,
                        "scope": url,
                        "evidence": f"Informational route {url} contains {len(comm_ctas)} commercial CTAs ({', '.join(str(c.get('text') if isinstance(c, dict) else getattr(c, 'text', '')) for c in comm_ctas[:3])}).",
                        "impact": "Generative search engines (Perplexity, Claude) penalize heavily promotional passages, reducing citation likelihood.",
                        "suggested_action": {
                            "summary": "Limit transactional promotional callouts on informational and educational pages to 1 primary CTA.",
                            "technical_fix": "Relocate aggressive promotional popups and inline buttons to a subtle footer or sidebar module.",
                            "creative_fix": "Maintain objective, educational tone throughout informational and technical guides.",
                            "priority": "medium",
                            "verification": "Verify informational passages maintain focus on answers with at most 1 conversion link.",
                        },
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
                    "url": url,
                    "scope": url,
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
        if hedge_density > 0.5 and (total_words >= 25 or len(hedge_matches) >= 3):
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
                    "url": url,
                    "scope": url,
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

        # 3.1 Freshness & Recency Sensor (industry analysis: recency correlates with AI citation frequency)
        if ptype in ("article", "content", "blog", "product_detail") and total_words >= 150:
            date_raw = parser.modified_date or parser.published_date
            if not date_raw:
                recommendations.append(
                    {
                        "id": "PROACTIVE.GEO.VISIBLE_RECENCY_DATE.001",
                        "title": "Publish visible last-updated dates on substantive content",
                        "category": "content",
                        "summary": f"Substantive page {url} lacks visible publication or modification dates. Generative search engines deprioritize undated content; pages updated within 3 months are cited more frequently across multiple industry analyses.",
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

        # Construct deterministic page-level content improvement plan
        gaps = []
        immediate_actions = []
        text_actions = []

        if depth_score < 3:
            gaps.append(f"Deficient mechanistic depth: only {depth_score} causal connector(s) detected (target: >= 3).")
            text_actions.append(
                "Inject causal explanatory conjunctions ('because', 'therefore', 'enables', 'results in') to explain the technical mechanisms behind stated benefits."
            )

        if len(stat_matches) == 0:
            gaps.append("Zero quantifiable statistics or benchmark metrics detected in body text.")
            text_actions.append(
                "Substantiate product/service claims with at least 2 quantifiable statistics (e.g. benchmark figures, percentages, verified metrics)."
            )

        if hedge_density > 0.5:
            gaps.append(
                f"Excessive epistemic hedge density: {hedge_density:.1f}% (target: <= 0.5%). Found {len(hedge_matches)} hedge expression(s)."
            )
            text_actions.append(
                f"Eliminate {len(hedge_matches)} detected hedge qualifiers ({', '.join(set(m.lower() for m in hedge_matches[:4]))}) and replace with affirmative, verified propositions."
            )

        if ftr < 0.080 and total_words >= 100:
            gaps.append(
                f"Low atomic fact-to-token ratio: {ftr:.3f} (target: >= 0.080). Contains {atomic_facts} atomic proposition(s) across {total_words} words."
            )
            text_actions.append(
                "Increase factual proposition density by pairing every qualitative adjective with a specific date, number, or benchmark."
            )

        if not has_lead_definition and total_words >= 150:
            gaps.append("Missing Bottom Line Up Front (BLUF) direct definition in the first 250 words.")
            immediate_actions.append(
                "Insert a 40-60 word definitive BLUF answer paragraph immediately below the primary H1."
            )

        if parser.tables == 0 and parser.lists == 0:
            gaps.append("Zero semantic comparison tables or structured specification lists found.")
            immediate_actions.append(
                "Convert feature lists and product specifications into a semantic <table> or <dl> definition list."
            )

        if not has_questions:
            gaps.append("Zero question-oriented headings (What/Why/How) detected.")
            immediate_actions.append(
                "Restructure H2 headings into conversational user query questions ('What is...', 'How does... work?')."
            )

        if exophoric_leads:
            gaps.append(
                f"Ambiguous exophoric opening pronouns ({len(exophoric_leads)} detected) break standalone passage attribution."
            )
            text_actions.append(
                "Replace leading pronouns ('It provides', 'They allow') in section leads with explicit canonical entity names."
            )

        if ptype == "article" and not has_auth_citation and total_words > 200:
            gaps.append("Missing outbound citations to primary authoritative sources (.edu, .gov, wikipedia.org, doi.org).")
            immediate_actions.append(
                "Add outbound hyperlinks to at least 2 primary research or regulatory sources to anchor claims."
            )

        if ptype == "article" and not has_credentials and total_words > 150:
            gaps.append("Missing named author credentials and E-E-A-T byline markup.")
            immediate_actions.append(
                "Embed an author byline box with verified professional credentials (MD, PhD, title) and Schema.org Person markup."
            )

        if evidence_genre_data["standalone_faq_deficit"]:
            gaps.append("Standalone FAQ format lacks supporting empirical evidence genres (Zhang et al. 2026 -5.7% citation penalty).")
            text_actions.append("Reinforce FAQ answers with concrete data points, comparison tables, or code blocks.")

        if kw_stuffing_data["is_stuffed"]:
            gaps.append(
                f"Unnatural keyword concentration: term '{kw_stuffing_data['top_repeated_words'][0][0]}' exceeds 4.5% density (-8.3% to -10% LLM degradation)."
            )
            text_actions.append("Diversify vocabulary and prune repetitive keyword instances to restore natural token distribution.")

        if (
            ptype in ("article", "content", "product_detail")
            and total_words >= 150
            and attributed_quotes_data["attributed_quotes"] == 0
        ):
            gaps.append("Zero attributed expert quotations detected (missing Princeton KDD 2024 +40.9% PAWC lift).")
            immediate_actions.append("Incorporate at least one blockquote attributing empirical insights to a credentialed specialist.")

        if ptype in ("article", "content", "product_detail") and total_words >= 250 and not has_lead_definition:
            gaps.append("Core resolution proposition absent from top 30% of document (Stanford 'Lost in the Middle').")
            immediate_actions.append("Front-load direct answer proposition into the first 50-75 words under primary heading.")

        chunking_plan = (
            "Divide body copy into modular 120-180 word passage chunks under question headings, each opening with a direct declarative claim."
            if total_words > 250
            else "Expand passage length to at least 150 words to provide sufficient semantic context for neural passage retrieval."
        )

        plan_priority = "high" if citability["total"] < 50 else ("medium" if citability["total"] < 75 else "low")

        page_plan = {
            "url": url,
            "page_url": url,
            "page_type": ptype,
            "word_count": total_words,
            "citability_score": citability["total"],
            "current_citability_score": citability["total"],
            "target_citability_score": 80,
            "dimension_scores": {
                "answer_block_quality": citability["answer_block_quality"],
                "self_containment": citability["self_containment"],
                "structural_readability": citability["structural_readability"],
                "statistical_density": citability["statistical_density"],
                "uniqueness_signals": citability["uniqueness_signals"],
                "evidence_genres_score": citability.get("evidence_genres_score", 0),
                "attributed_quotes_score": citability.get("attributed_quotations_score", 0),
                "bluf_primacy_score": citability.get("bluf_primacy_score", 0),
                "mechanistic_depth_score": depth_score,
                "atomic_fact_ratio": ftr,
                "hedge_density_pct": round(hedge_density, 2),
            },
            "evidence_genres": {
                "detected": evidence_genre_data["genres_detected"],
                "count": evidence_genre_data["genre_count"],
                "standalone_faq_deficit": evidence_genre_data["standalone_faq_deficit"],
            },
            "attributed_quotations": {
                "total_quotes": attributed_quotes_data["total_quotes"],
                "attributed_quotes": attributed_quotes_data["attributed_quotes"],
                "has_named_expert": attributed_quotes_data["has_named_expert"],
            },
            "bluf_placement": {
                "present_in_top_30_pct": bluf_data["bluf_present_in_top30"],
                "lead_word_count": bluf_data["lead_word_count"],
            },
            "keyword_stuffing": {
                "is_stuffed": kw_stuffing_data["is_stuffed"],
                "max_density": kw_stuffing_data["max_density"],
            },
            "gap_analysis": gaps if gaps else ["Content meets or exceeds baseline citability thresholds across evaluated dimensions."],
            "prescribed_actions": {
                "immediate_structural_actions": immediate_actions if immediate_actions else ["Maintain current structural heading and table layout."],
                "textual_modifications": text_actions if text_actions else ["Continue maintaining high factual density and assertive phrasing."],
                "passage_chunking_plan": chunking_plan,
            },
            "priority": plan_priority,
            "epistemic_qualification": (
                "This content improvement plan is deterministically synthesized from empirical static text citability heuristics "
                "(Princeton KDD 2024, AutoGEO, C-SEO Bench). It measures structural, linguistic, and informational citability readiness, "
                "not live search engine citation logs or dynamic LLM inference results."
            ),
        }
        page_improvement_plans.append(page_plan)

    avg_cit = (
        round(sum(c["total"] for c in page_citability_map.values()) / max(len(page_citability_map), 1), 1)
        if page_citability_map
        else 0.0
    )

    geo_citability_summary = {
        "average_citability_score": avg_cit,
        "pages_analyzed": len(target_pages),
        "evidence_genres_distribution": {
            genre: sum(
                1 for p in page_improvement_plans if genre in p.get("evidence_genres", {}).get("detected", [])
            )
            for genre in ["code", "statistics", "definition_copula", "comparison_table", "procedural_steps"]
        },
        "pages_with_attributed_quotes": sum(
            1 for p in page_improvement_plans if p.get("attributed_quotations", {}).get("attributed_quotes", 0) > 0
        ),
        "pages_with_bluf_alignment": sum(
            1 for p in page_improvement_plans if p.get("bluf_placement", {}).get("present_in_top_30_pct", False)
        ),
        "pages_with_keyword_stuffing": sum(
            1 for p in page_improvement_plans if p.get("keyword_stuffing", {}).get("is_stuffed", False)
        ),
    }

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "page_improvement_plans": page_improvement_plans,
        "geo_citability_summary": geo_citability_summary,
        "coverage": {
            "target_pages_evaluated": len(target_pages),
            "average_citability_score": avg_cit,
            "improvement_plans_generated": len(page_improvement_plans),
        },
        "limitations": [
            "Content improvement plans are derived deterministically from static text citability heuristics "
            "(Princeton KDD 2024, AutoGEO, C-SEO Bench). These heuristics evaluate passage structure, factual density, "
            "and linguistic assertiveness; they do not measure live search engine citation logs or dynamic LLM inference results."
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generative Engine Optimization (GEO) & Citability Diagnostic Sensor.\n"
            "Deterministically scores web content against the 9 empirical Princeton KDD 2024 / AutoGEO vectors: "
            "causal mechanisms (+28% preference), statistical evidence density (+40% lift), attributed expert quotations "
            "(+40.9% lift), BLUF top-30% placement, standalone FAQ penalties (-5.7%), keyword stuffing perplexity degradation, "
            "and synthesizes deterministic 120-180 word passage improvement plans."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--inventory", required=False, help="Path to pre-crawled site inventory JSON (inv.json) for offline execution")
    parser.add_argument("--state", help="Path to global state JSON (optional multi-turn evaluation)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output serialization format (default: json)")
    args = parser.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    domain = p.netloc

    if args.inventory:
        if os.path.exists(args.inventory):
            try:
                with open(args.inventory, "r", encoding="utf-8") as f:
                    inv = json.load(f)
            except Exception as e:
                inv = {"pages": [], "error": f"Failed to parse inventory: {e}", "status": "inconclusive"}
        else:
            inv = {"pages": [], "error": "Inventory file not found", "status": "inconclusive"}
    else:
        status, html, _, _ = safe_fetch(base)
        if status == 200 and html:
            inv = {
                "site": domain,
                "pages": [
                    {"url": base, "status": 200, "content_type": "text/html", "page_type": "article", "html": html}
                ],
            }
        else:
            inv = {"site": domain, "pages": []}

    res = audit(base, domain, inv, state_file=args.state)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
