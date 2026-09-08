"""Trafilatura and Crawl4AI inspired evidence extraction and boilerplate stripping.

Provides:
- Trafilatura-style boilerplate removal (layout chrome, headers, footers, nav).
- Crawl4AI-style LLM-friendly clean Markdown generation.
- Signal-to-Noise Ratio (SNR) calculation.
- Honest rendering observation detection (sparse SPA shell detection without browser escalation).
- Atomic fact candidates and causal/statistical claim proposition extraction.
Pure Python standard library (re).
"""

from __future__ import annotations

import re
from typing import List, Tuple

from .models import ClaimCandidate, FactCandidate, Heading, Observation, TableData


class EvidenceExtractor:
    """Extracts structured facts, clean Markdown, and epistemic observations from HTML."""

    CURRENCY_MAP = {
        "$": "USD",
        "USD": "USD",
        "€": "EUR",
        "EUR": "EUR",
        "£": "GBP",
        "GBP": "GBP",
        "¥": "JPY",
        "JPY": "JPY",
        "₹": "INR",
        "INR": "INR",
    }

    INTERVAL_MAP = {
        "mo": "monthly",
        "month": "monthly",
        "yr": "yearly",
        "year": "yearly",
        "user": "per_user",
        "day": "daily",
        "week": "weekly",
    }

    PRICE_REGEX = re.compile(
        r"(?P<currency>[\$\€\£\¥\₹]|USD|EUR|GBP|JPY|INR)\s*(?P<amount>\d{1,6}(?:,\d{3})*(?:\.\d{2})?)\s*(?:/(?P<interval>mo|month|yr|year|user|day|week))?",
        re.IGNORECASE,
    )
    PHONE_REGEX = re.compile(
        r"(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{2,9}"
    )
    EMAIL_REGEX = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )
    STAT_REGEX = re.compile(
        r"\b(?:\d{1,3}(?:\.\d+)?%|\d+(?:\.\d+)?x|\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b"
    )
    CAUSAL_CONNECTORS = [
        "because",
        "due to",
        "as a result of",
        "which leads to",
        "which enables",
        "consequently",
        "therefore",
        "resulting in",
    ]

    SPA_SHELL_INDICATORS = [
        r'<div\s+id=["\'](?:root|app|__next)["\']>\s*</div>',
        r'<div\s+id=["\']root["\']\s*/>',
        r'<div\s+id=["\']app["\']\s*/>',
        r'You need to enable JavaScript to run this app',
    ]

    @classmethod
    def strip_boilerplate(cls, raw_html: str) -> str:
        """Strips layout chrome (scripts, styles, nav, headers, footers, aside, svgs, hidden elements, and cookie banners)."""
        if not raw_html:
            return ""

        text = raw_html
        # Remove non-content tags and their inner content
        for tag in ["script", "style", "noscript", "svg", "header", "nav", "footer", "aside", "template"]:
            text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", text, flags=re.IGNORECASE | re.DOTALL)

        # Remove hidden containers, aria-hidden nodes, and cookie/consent banners
        text = re.sub(r"<([a-zA-Z0-9]+)[^>]*?\b(?:hidden|aria-hidden=['\"]true['\"])[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<([a-zA-Z0-9]+)[^>]*?style=['\"][^'\"]*?display:\s*none[^'\"]*?['\"][^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<([a-zA-Z0-9]+)[^>]*?(?:class|id)=['\"][^'\"]*?(?:cookie|consent|onetrust)[^'\"]*?['\"][^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)

        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(clean_lines)

    @classmethod
    def calculate_text_density_ratio(cls, clean_text: str, raw_html: str) -> float:
        """Calculates Text Density Ratio (clean text bytes / raw HTML bytes)."""
        html_bytes = len(raw_html.encode("utf-8"))
        if html_bytes == 0:
            return 0.0
        clean_bytes = len(clean_text.encode("utf-8"))
        return round(clean_bytes / float(html_bytes), 4)

    # Backward-compatible alias for existing references
    calculate_snr = calculate_text_density_ratio

    @classmethod
    def detect_rendering_limitations(
        cls, raw_html: str, clean_text: str, source_url: str
    ) -> List[Observation]:
        """Detects whether client-side JavaScript rendering is required without escalating to a browser."""
        observations: List[Observation] = []
        word_count = len(clean_text.split())
        html_size = len(raw_html)

        # Check for classic empty SPA mounting containers
        is_empty_spa = any(re.search(pat, raw_html, re.IGNORECASE) for pat in cls.SPA_SHELL_INDICATORS)

        if is_empty_spa and word_count < 60:
            observations.append(
                Observation(
                    type="rendering_observation",
                    value="server_html_appears_sparse",
                    confidence="high",
                    evidence=(
                        f"Target {source_url} returns an empty SPA shell "
                        f"({word_count} visible words, HTML size {html_size} bytes). "
                        "Critical content is likely client-side rendered via JavaScript."
                    ),
                    severity_hint="critical",
                )
            )
        elif html_size > 30000 and word_count < 40:
            observations.append(
                Observation(
                    type="rendering_observation",
                    value="server_html_appears_sparse",
                    confidence="medium",
                    evidence=(
                        f"Heavy HTML envelope ({html_size} bytes) on {source_url} yielded only "
                        f"{word_count} visible words, suggesting client-side hydration dependency."
                    ),
                    severity_hint="high",
                )
            )

        return observations

    @classmethod
    def build_clean_markdown(
        cls,
        title: str,
        headings: List[Heading],
        clean_text: str,
        tables: List[TableData],
        code_blocks: List[str],
    ) -> str:
        """Produces token-efficient, LLM-friendly Markdown representation."""
        md_parts: List[str] = []

        if title:
            md_parts.append(f"# {title}\n")

        # Add structured tables
        for idx, table in enumerate(tables, 1):
            if table.headers or table.rows:
                md_parts.append(f"### Table {idx}")
                if table.headers:
                    md_parts.append("| " + " | ".join(table.headers) + " |")
                    md_parts.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
                for row in table.rows:
                    md_parts.append("| " + " | ".join(row) + " |")
                md_parts.append("")

        # Add code blocks
        for block in code_blocks:
            md_parts.append("```\n" + block + "\n```\n")

        # Add main text
        if clean_text:
            md_parts.append("## Main Content\n")
            md_parts.append(clean_text)

        return "\n".join(md_parts)

    @classmethod
    def extract_facts_and_claims(
        cls, clean_text: str, source_url: str
    ) -> Tuple[List[FactCandidate], List[ClaimCandidate]]:
        """Extracts candidate facts and causal/statistical claim propositions from text."""
        facts: List[FactCandidate] = []
        claims: List[ClaimCandidate] = []

        if not clean_text:
            return facts, claims

        # Price facts
        for match in cls.PRICE_REGEX.finditer(clean_text):
            try:
                raw_amt = match.group("amount").replace(",", "")
                price_val = float(raw_amt)
                raw_curr = match.group("currency")
                currency = cls.CURRENCY_MAP.get(raw_curr.upper(), raw_curr) if raw_curr else "USD"
                raw_interval = match.group("interval")
                interval = cls.INTERVAL_MAP.get(raw_interval.lower(), raw_interval) if raw_interval else None
                facts.append(
                    FactCandidate(
                        attribute="price",
                        value=price_val,
                        currency=currency,
                        interval=interval,
                        source_url=source_url,
                        locator="visible_text",
                        mechanism="visible_text",
                    )
                )
            except (ValueError, AttributeError):
                pass

        # Contact facts
        for match in cls.EMAIL_REGEX.finditer(clean_text):
            facts.append(
                FactCandidate(
                    attribute="email",
                    value=match.group(0),
                    source_url=source_url,
                    locator="visible_text",
                    mechanism="visible_text",
                )
            )

        for match in cls.PHONE_REGEX.finditer(clean_text):
            phone_str = match.group(0).strip()
            digits_only = re.sub(r"\D", "", phone_str)
            if 7 <= len(digits_only) <= 15:
                facts.append(
                    FactCandidate(
                        attribute="phone",
                        value=phone_str,
                        source_url=source_url,
                        locator="visible_text",
                        mechanism="visible_text",
                    )
                )

        # Causal and statistical claims
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", clean_text) if len(s.strip()) > 25]
        for sent in sentences:
            has_stat = bool(cls.STAT_REGEX.search(sent))
            causal_hit = next((conn for conn in cls.CAUSAL_CONNECTORS if conn in sent.lower()), None)

            if has_stat or causal_hit:
                claims.append(
                    ClaimCandidate(
                        claim_text=sent,
                        causal_type=causal_hit,
                        statistical_proposition=has_stat,
                        source_url=source_url,
                    )
                )

        return facts, claims
