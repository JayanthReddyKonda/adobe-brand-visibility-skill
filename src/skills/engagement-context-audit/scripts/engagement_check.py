#!/usr/bin/env python3
"""engagement_check.py - Engagement, Scent & Intent Handoff Diagnostic Sensor.

Evaluates post-citation landing page orientation, CTA reachability index,
viewport answer anchoring, and cognitive reading load under zero-dependency stdlib.
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from safe_fetch import safe_fetch  # type: ignore
except ImportError:
    safe_fetch = None  # type: ignore

COMMERCIAL_ACTION_PATTERNS = re.compile(
    r"\b(buy|order|cart|checkout|subscribe|sign up|sign up today|start free trial|book demo|contact sales|request demo|get started|purchase|try free|pricing|free trial)\b",
    re.IGNORECASE,
)
MARKETING_FLUFF_PATTERNS = re.compile(
    r"\b(game-changer|delve|revolutionize|spearhead|testament to|unleash|beacon of|tapestry|multifaceted|cutting-edge|seamless|world-class|next-level)\b",
    re.IGNORECASE,
)
GENERIC_H1_TERMS = {"welcome", "home", "main", "untitled", "test", "page", "index", "default"}


class EngagementDOMParser(HTMLParser):
    """Zero-dependency HTML parser extracting headings, interactive elements, and viewport text."""

    def __init__(self):
        super().__init__()
        self.in_script = False
        self.title = ""
        self.in_title = False
        self.h1_list: List[str] = []
        self.h2_list: List[str] = []
        self.current_tag: Optional[str] = None
        self.current_text: List[str] = []
        self.body_text: List[str] = []
        self.nav_links: List[str] = []
        self.nav_link_texts: List[str] = []
        self.in_anchor = False
        self.current_anchor_text: List[str] = []
        self.current_href = ""
        self.ctas: List[str] = []
        self.meta_tags: Dict[str, str] = {}
        self.in_button = False
        self.current_button_text: List[str] = []
        self.current_is_cta = False
        self.cta_texts: List[str] = []
        self.in_p = False
        self.current_p_text: List[str] = []
        self.paragraphs: List[str] = []
        self.interactive_elements: List[Dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower in ("script", "style", "noscript"):
            self.in_script = True
        elif tag_lower == "meta":
            prop = attr_dict.get("property", attr_dict.get("name", "")).lower()
            content = attr_dict.get("content", "").strip()
            if prop and content:
                self.meta_tags[prop] = content
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower in ("h1", "h2"):
            self.current_tag = tag_lower
            self.current_text = []
        elif tag_lower == "p":
            self.in_p = True
            self.current_p_text = []
        elif tag_lower == "button":
            self.in_button = True
            self.current_button_text = []
        elif tag_lower == "input":
            itype = attr_dict.get("type", "").lower()
            if itype in ("submit", "button"):
                val = attr_dict.get("value", "").strip() or attr_dict.get("aria-label", "").strip()
                if val:
                    self.cta_texts.append(val)
                    is_comm = bool(COMMERCIAL_ACTION_PATTERNS.search(val))
                    self.interactive_elements.append(
                        {"tag": "input", "text": val, "href": "", "is_commercial_cta": is_comm}
                    )
        elif tag_lower in ("div", "span") and attr_dict.get("role", "").lower() == "button":
            self.in_button = True
            self.current_button_text = []
        elif tag_lower == "a":
            self.in_anchor = True
            self.current_anchor_text = []
            self.current_href = attr_dict.get("href", "")
            self.current_is_cta = False
            if self.current_href:
                self.nav_links.append(self.current_href)
                cls = attr_dict.get("class", "").lower()
                role = attr_dict.get("role", "").lower()
                if any(x in cls for x in ("btn", "button", "cta", "action")) or role == "button":
                    self.ctas.append(self.current_href)
                    self.current_is_cta = True

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript"):
            self.in_script = False
        elif tag_lower == "title":
            self.in_title = False
        elif tag_lower == "h1":
            if self.current_text:
                self.h1_list.append(" ".join(self.current_text).strip())
            self.current_tag = None
        elif tag_lower == "h2":
            if self.current_text:
                self.h2_list.append(" ".join(self.current_text).strip())
            self.current_tag = None
        elif tag_lower == "p":
            self.in_p = False
            ptxt = " ".join(self.current_p_text).strip()
            if ptxt:
                self.paragraphs.append(ptxt)
            self.current_p_text = []
        elif tag_lower in ("button", "div", "span"):
            if self.in_button and self.current_button_text:
                b_text = " ".join(self.current_button_text).strip()
                if b_text:
                    self.cta_texts.append(b_text)
                    is_comm = bool(COMMERCIAL_ACTION_PATTERNS.search(b_text))
                    self.interactive_elements.append(
                        {"tag": tag_lower, "text": b_text, "href": "", "is_commercial_cta": is_comm}
                    )
            if tag_lower == "button" or self.in_button:
                self.in_button = False
        elif tag_lower == "a":
            if self.in_anchor and self.current_anchor_text:
                a_text = " ".join(self.current_anchor_text).strip()
                self.nav_link_texts.append(a_text)
                is_comm = bool(COMMERCIAL_ACTION_PATTERNS.search(a_text)) or self.current_is_cta
                self.interactive_elements.append(
                    {"tag": "a", "text": a_text, "href": self.current_href, "is_commercial_cta": is_comm}
                )
                if (self.current_is_cta or is_comm) and a_text:
                    self.cta_texts.append(a_text)
            self.in_anchor = False

    def handle_data(self, data: str):
        if self.in_title:
            self.title += " " + data.strip()
        if self.current_tag in ("h1", "h2"):
            self.current_text.append(data.strip())
        if self.in_p:
            self.current_p_text.append(data.strip())
        if self.in_button:
            self.current_button_text.append(data.strip())
        if self.in_anchor:
            self.current_anchor_text.append(data.strip())
        if not self.in_script:
            txt = data.strip()
            if txt:
                self.body_text.append(txt)


def compute_viewport_answer_anchoring(dom: EngagementDOMParser, full_text: str, page_type: str, facts: Optional[dict] = None) -> dict:
    """Evaluate whether arriving visitors encounter immediate answer propositions in the opening viewport."""
    lead_paragraphs = dom.paragraphs[:2] if dom.paragraphs else []
    lead_text = " ".join(lead_paragraphs) or " ".join(full_text.split()[:150])
    lead_lower = lead_text.lower()
    missing_propositions = []
    anchored = True

    if page_type == "pricing":
        if not re.search(r"(?:\$|€|£|¥|\d+\.\d{2}|\b(?:free|starter|pro|tier|plan|month|annual)\b)", lead_lower):
            anchored = False
            missing_propositions.append("pricing_figures_or_tiers")
    elif page_type in ("product", "product_detail"):
        if not re.search(r"\b(?:is|provides|enables|offers|designed for|allows|features|built for)\b", lead_lower):
            anchored = False
            missing_propositions.append("product_core_functionality")
    elif page_type in ("article", "documentation") and not re.search(r"\b(?:is|are|means|refers to|defined as|explains|provides)\b", lead_lower):
        anchored = False
        missing_propositions.append("direct_answer_definition")

    return {
        "anchored_in_viewport": anchored,
        "lead_words_count": len(lead_text.split()),
        "missing_propositions": missing_propositions,
        "lead_snippet": lead_text[:120],
    }


def compute_cta_reachability_index(dom: EngagementDOMParser) -> dict:
    """Evaluate reachability index = 1 / (1 + preceding interactive elements before primary commercial CTA)."""
    elements = dom.interactive_elements
    first_comm_idx = None
    first_comm_text = ""
    inert_ctas: List[Dict[str, str]] = []

    for idx, el in enumerate(elements):
        if el.get("is_commercial_cta"):
            if first_comm_idx is None:
                first_comm_idx = idx
                first_comm_text = el.get("text", "")
            href = (el.get("href") or "").strip()
            if href in ("#", "", "javascript:void(0)", "javascript:;", "javascript:void(0);") or href.startswith("javascript:"):
                inert_ctas.append({"text": el.get("text", ""), "href": href})

    if first_comm_idx is None:
        return {
            "first_commercial_cta_index": None,
            "preceding_interactive_elements": len(elements),
            "reachability_score": 0.0,
            "is_delayed": True,
            "first_cta_text": "",
            "inert_ctas": inert_ctas,
        }

    reachability_score = round(1.0 / (1.0 + first_comm_idx), 3)
    return {
        "first_commercial_cta_index": first_comm_idx,
        "preceding_interactive_elements": first_comm_idx,
        "reachability_score": reachability_score,
        "is_delayed": first_comm_idx > 3,
        "first_cta_text": first_comm_text,
        "inert_ctas": inert_ctas,
    }


def check_fake_or_inaccessible_forms(html: str, url: str) -> Optional[Dict[str, Any]]:
    """Detect modal sign-in or form triggers pointing to empty/inaccessible containers."""
    if not html:
        return None
    dialog_matches = re.finditer(
        r'<(?:div|dialog|form)\b[^>]*id=["\']([^"\']*(?:login|signin|signup|modal|dialog)[^"\']*)["\'][^>]*>(.*?)</(?:div|dialog|form)>',
        html,
        re.DOTALL | re.I,
    )
    for m in dialog_matches:
        container_id = m.group(1)
        body = m.group(2)
        inputs = re.findall(r"<input\b", body, re.I)
        if len(inputs) == 0 and len(body.strip()) < 100:
            return make_finding(
                "INACCESSIBLE_INTERACTIVE_DIALOG",
                f"Interactive dialog container #{container_id} is non-functional (0 input fields)",
                "high",
                url,
                f"Interactive element targets #{container_id} which contains 0 input elements in raw HTML.",
            )
    return None


def check_broken_component_integrations(html_content: str, url: str) -> Optional[Dict[str, Any]]:
    """EN2: Detect broken third-party components (e.g. Google Maps API errors) failing in initial/rendered DOM."""
    map_error = bool(re.search(r"This page can['’]t load Google Maps correctly", html_content, re.I))
    gm_err = bool(re.search(r'\b(?:gm-err-container|gm-err-message)\b', html_content, re.I))
    if map_error or gm_err:
        return {
            "id": "EN2_COMPONENT_LOADING_FAILURE",
            "cause_id": "COMPONENT_LOADING_FAILURE",
            "check_id": "EN2",
            "title": f"Interactive map component displays runtime loading error on {url}",
            "severity": "medium",
            "category": "engagement",
            "confidence": "high",
            "scope": url,
            "evidence": {
                "summary": f"Interactive Google Maps component on {url} displays: 'This page can\\'t load Google Maps correctly.'",
                "sources": [{"url": url, "observation": "Google Maps runtime configuration failure (missing API key or referrer mismatch)"}],
            },
            "root_cause": "Embedded map widget is missing a valid API key, billing setup, or authorized HTTP referrer.",
            "impact": "Visitors seeking physical store locations encounter broken visual errors rather than store directions.",
            "suggested_action": {
                "summary": "Configure valid map API key or provide static accessible location fallback.",
                "technical_fix": "Supply a valid Google Maps JavaScript API key and embed static address text alongside the map.",
                "creative_fix": "Ensure physical store addresses and operating hours remain readable if external scripts fail.",
                "priority": "medium",
                "verification": f"Verify map container on {url} renders without error banners.",
            },
        }
    return None


def check_unnamed_interactive_controls(html_content: str, url: str) -> Optional[Dict[str, Any]]:
    """EN6: Control representation - detect interactive buttons with empty text and no accessible name."""
    unnamed_buttons = 0
    for btn_match in re.finditer(r"<button\b([^>]*)>(.*?)</button>", html_content, re.DOTALL | re.I):
        attrs_str = btn_match.group(1)
        inner_content = btn_match.group(2)
        has_label = bool(re.search(r'\b(?:aria-label|aria-labelledby|title)=["\'][^"\']+["\']', attrs_str, re.I))
        if has_label:
            continue
        text_only = re.sub(r"<[^>]+>", " ", inner_content).strip()
        if text_only:
            continue
        img_has_alt = bool(re.search(r'<img\b[^>]*\balt=["\'][^"\']+["\']', inner_content, re.I))
        if img_has_alt:
            continue
        unnamed_buttons += 1

    if unnamed_buttons >= 2:
        return {
            "id": "EN6_UNNAMED_INTERACTIVE_CONTROL",
            "cause_id": "CONTROL_REPRESENTATION_GAP",
            "check_id": "EN6",
            "title": f"Product action controls lack accessible names ({unnamed_buttons} unnamed buttons on {url})",
            "severity": "medium",
            "category": "engagement",
            "confidence": "high",
            "scope": url,
            "evidence": {
                "summary": f"Found {unnamed_buttons} interactive <button> elements with empty text and no aria-label or title attributes on {url}.",
                "sources": [{"url": url, "observation": f"{unnamed_buttons} action buttons expose no name to assistive tech or machine agents"}],
            },
            "root_cause": "Icon-only buttons (such as cart or wishlist) omit accessible text or aria-label attributes.",
            "impact": "Assistive screen readers, conversational agents, and automated buying bots cannot determine control purpose.",
            "suggested_action": {
                "summary": "Add explicit aria-label attributes to all icon-only action buttons.",
                "technical_fix": "Add aria-label=\"Add to cart\" or aria-label=\"Add to wishlist\" to <button> elements.",
                "creative_fix": "Ensure all interactive shopping controls communicate their clear intent.",
                "priority": "medium",
                "verification": f"Verify all buttons on {url} possess accessible names in the DOM accessibility tree.",
            },
        }
    return None


def compute_information_scent(h1_text: str, lead_text: str) -> dict:
    """Measure information scent purity between heading and lead content."""
    combined = f"{h1_text} {lead_text}".strip()
    words = re.findall(r"\b[a-zA-Z]{3,}\b", combined.lower())
    if not words:
        return {"scent_ratio": 1.0, "fluff_matches": [], "is_diluted": False}

    fluff_found = MARKETING_FLUFF_PATTERNS.findall(combined)
    fluff_ratio = len(fluff_found) / max(len(words), 1)
    is_diluted = fluff_ratio > 0.03 or len(fluff_found) >= 2
    scent_ratio = round(max(0.0, 1.0 - (fluff_ratio * 10)), 2)

    return {"scent_ratio": scent_ratio, "fluff_matches": list(set(f.lower() for f in fluff_found)), "is_diluted": is_diluted}


def compute_cognitive_readability(text: str) -> dict:
    """Compute Automated Readability Index (ARI) to evaluate cognitive load for citation traffic."""
    words = re.findall(r"\b\w+\b", text)
    if not words:
        return {"ari_score": 0.0, "avg_sentence_length": 0.0, "is_complex": False}

    characters = sum(len(w) for w in words)
    sentences = max(1, len(re.split(r"[.!?]+", text)) - 1)
    word_count = len(words)
    ari = 4.71 * (characters / word_count) + 0.5 * (word_count / sentences) - 21.43
    ari_score = round(max(0.0, ari), 1)
    return {
        "ari_score": ari_score,
        "avg_sentence_length": round(word_count / sentences, 1),
        "is_complex": ari_score > 15.0 or (word_count / sentences) > 30.0,
    }


def make_finding(cause_id: str, title: str, severity: str, scope: str, evidence: Any, root_cause: str = "", category: str = "engagement") -> Dict[str, Any]:
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
        "impact": f"Degrades post-citation visitor orientation and conversion: {title}",
        "suggested_action": {
            "summary": f"Remediate {cause_id} on {scope}",
            "technical_fix": f"Reorganize DOM elements and heading structure for {cause_id}.",
            "creative_fix": f"Streamline intent scent and foreground immediate value actions on {scope}.",
            "priority": severity,
            "verification": f"Verify reachability and orientation metrics on {scope}.",
        },
    }


def audit_page_engagement(
    html_content: str,
    url: str,
    page_type: str = "general",
    state: Optional[dict] = None,
    page_dict: Optional[dict] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Audit single HTML page for engagement and intent continuity."""
    findings: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    dom = EngagementDOMParser()
    try:
        dom.feed(html_content)
    except Exception as e:
        return [make_finding("HTML_PARSING_FAILED", "HTML parsing failed", "low", url, str(e))], [], {"visible_words": 0}

    full_text = " ".join(dom.body_text)
    words = full_text.split()
    lead_h1 = dom.h1_list[0] if dom.h1_list else ""
    lead_text = " ".join(dom.paragraphs[:2]) if dom.paragraphs else ""

    # Multilingual commercial action keywords
    all_actions = " ".join(dom.nav_link_texts + dom.cta_texts).lower()
    has_price = bool(re.search(r"(?:\$|€|£|¥|\bUSD\b|\bEUR\b)\s*\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:\$|€|£|¥)", html_content))
    if has_price:
        has_trans = any(w in all_actions for w in (
            "buy", "cart", "checkout", "subscribe", "order", "shop", "get started",
            "comprar", "compra", "mostrar", "carrito", "pedir", "acheter", "panier", "kaufen", "warenkorb"
        ))
        if not has_trans:
            findings.append(make_finding(
                "INTENT_TO_LANDING_MISMATCH",
                "Pricing intent journey lacks explicit commercial continuation",
                "medium",
                url,
                f"Page {url} has pricing facts but lacks transactional CTA.",
            ))

    # 1. H1 orientation check
    if not lead_h1:
        findings.append(make_finding("VALUE_PROPOSITION_ORIENTATION_VACUUM", "Primary heading (H1) missing from page", "high", url, f"Page {url} has no H1 element"))
    elif lead_h1.lower() in GENERIC_H1_TERMS:
        findings.append(make_finding("LOW_INFORMATION_SCENT", f"Generic H1 heading '{lead_h1}' dilutes scent", "medium", url, f"Generic heading: '{lead_h1}'"))

    # 2. CTA reachability check
    cta_reach = compute_cta_reachability_index(dom)
    if cta_reach["is_delayed"]:
        findings.append(make_finding(
            "DELAYED_COMMERCIAL_CALL_TO_ACTION",
            "Primary commercial CTA delayed behind auxiliary elements",
            "medium",
            url,
            f"Commercial CTA delayed: index={cta_reach['first_commercial_cta_index']}",
        ))

    if cta_reach.get("inert_ctas"):
        icta = cta_reach["inert_ctas"][0]
        findings.append(make_finding(
            "INERT_CTA_TARGET",
            f"Commercial CTA targets inert destination (\"{icta['text']}\" -> {icta['href'] or 'empty'})",
            "high",
            url,
            f"Commercial call-to-action '{icta['text']}' has inert target '{icta['href']}', causing visitor conversion abandonment.",
        ))

    fake_form_f = check_fake_or_inaccessible_forms(html_content, url)
    if fake_form_f:
        findings.append(fake_form_f)

    comp_err_f = check_broken_component_integrations(html_content, url)
    if comp_err_f:
        findings.append(comp_err_f)

    unnamed_f = check_unnamed_interactive_controls(html_content, url)
    if unnamed_f:
        findings.append(unnamed_f)

    # 3. Viewport answer anchoring
    anchoring = compute_viewport_answer_anchoring(dom, full_text, page_type)
    if not anchoring["anchored_in_viewport"] and anchoring["missing_propositions"]:
        findings.append(make_finding(
            "BELOW_FOLD_ANSWER_DISPERSION",
            "Core answer proposition displaced below the fold",
            "medium",
            url,
            f"Missing in top viewport: {', '.join(anchoring['missing_propositions'])}",
        ))

    metrics = {
        "visible_words": len(words),
        "h1": bool(lead_h1),
        "cta_reachability_score": cta_reach["reachability_score"],
        "anchored_in_viewport": anchoring["anchored_in_viewport"],
        "dom": dom,
        "lead_h1": lead_h1,
        "lead_text": lead_text,
    }
    return findings, recommendations, metrics


def audit(
    base: str,
    domain: str,
    inv: Optional[Dict[str, Any]] = None,
    state_file: Optional[str] = None,
    target_url: Optional[str] = None,
    referrer_query: Optional[str] = None,
    viewport_only: bool = False,
) -> Dict[str, Any]:
    """Execute engagement and intent continuity sensor against inventory."""
    if isinstance(inv, (str, bytes, os.PathLike)) and os.path.exists(inv):
        try:
            with open(inv, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    elif not isinstance(inv, dict):
        inv = None

    pages = inv.get("pages", []) if isinstance(inv, dict) else []
    if not pages:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "engagement_continuity_summary": {"average_reachability_index": 0.0, "pages_analyzed": 0, "pages_delayed_cta": 0, "pages_missing_h1": 0},
        }

    if target_url:
        pages = [p for p in pages if p.get("url") == target_url] or pages

    findings = []
    reachability_scores = []
    delayed_ctas = 0
    missing_h1s = 0
    viewport_records = []
    evaluations = []

    for page in pages:
        url = page.get("url", "")
        html = page.get("html", "")
        ptype = page.get("page_type", "article")

        dom = EngagementDOMParser()
        try:
            dom.feed(html)
        except Exception:
            pass

        full_text = " ".join(dom.body_text)
        lead_h1 = dom.h1_list[0] if dom.h1_list else ""
        lead_text = " ".join(dom.paragraphs[:2]) if dom.paragraphs else ""

        # 1. H1 orientation check
        if not lead_h1:
            missing_h1s += 1
            findings.append(make_finding("VALUE_PROPOSITION_ORIENTATION_VACUUM", "Primary heading (H1) missing from page", "high", url, f"Page {url} has no H1 element"))
        elif lead_h1.lower() in GENERIC_H1_TERMS:
            findings.append(make_finding("LOW_INFORMATION_SCENT", f"Generic H1 heading '{lead_h1}' dilutes scent", "medium", url, f"Generic heading: '{lead_h1}'"))

        # 2. CTA reachability check
        cta_reach = compute_cta_reachability_index(dom)
        reachability_scores.append(cta_reach["reachability_score"])
        if cta_reach["is_delayed"]:
            delayed_ctas += 1
            findings.append(make_finding(
                "DELAYED_COMMERCIAL_CALL_TO_ACTION",
                "Primary commercial CTA delayed behind auxiliary elements",
                "medium",
                url,
                f"Commercial CTA delayed: index={cta_reach['first_commercial_cta_index']}, preceding={cta_reach['preceding_interactive_elements']}",
            ))

        if cta_reach.get("inert_ctas") and not any(f.get("cause_id") == "INERT_CTA_TARGET" and f.get("scope") == url for f in findings):
            icta = cta_reach["inert_ctas"][0]
            findings.append(make_finding(
                "INERT_CTA_TARGET",
                f"Commercial CTA targets inert destination (\"{icta['text']}\" -> {icta['href'] or 'empty'})",
                "high",
                url,
                f"Commercial call-to-action '{icta['text']}' has inert target '{icta['href']}', causing visitor conversion abandonment.",
            ))

        fake_form_f = check_fake_or_inaccessible_forms(html, url)
        if fake_form_f and not any(f.get("cause_id") == "INACCESSIBLE_INTERACTIVE_DIALOG" and f.get("scope") == url for f in findings):
            findings.append(fake_form_f)

        # 3. Viewport answer anchoring
        anchoring = compute_viewport_answer_anchoring(dom, full_text, ptype)
        if not anchoring["anchored_in_viewport"] and anchoring["missing_propositions"]:
            findings.append(make_finding(
                "BELOW_FOLD_ANSWER_DISPERSION",
                "Core answer proposition displaced below the fold",
                "medium",
                url,
                f"Missing in top viewport: {', '.join(anchoring['missing_propositions'])}",
            ))

        vp_rec = {
            "url": url,
            "page_type": ptype,
            "h1": lead_h1,
            "anchored_in_viewport": anchoring["anchored_in_viewport"],
            "reachability_score": cta_reach["reachability_score"],
            "first_cta_text": cta_reach["first_cta_text"],
        }
        viewport_records.append(vp_rec)

        if referrer_query:
            q_terms = set(re.findall(r"\b\w{3,}\b", referrer_query.lower()))
            h1_terms = set(re.findall(r"\b\w{3,}\b", lead_h1.lower()))
            lead_terms = set(re.findall(r"\b\w{3,}\b", lead_text.lower()))
            match_count = len(q_terms.intersection(h1_terms | lead_terms))
            scent_score = round(match_count / max(len(q_terms), 1), 2)
            evaluations.append({
                "url": url,
                "query": referrer_query,
                "h1_alignment": lead_h1,
                "scent_score": scent_score,
                "aligned": scent_score >= 0.5,
            })

    avg_reach = round(sum(reachability_scores) / max(len(reachability_scores), 1), 3)

    res: Dict[str, Any] = {
        "status": "ok",
        "engagement_continuity_summary": {
            "average_reachability_index": avg_reach,
            "pages_analyzed": len(pages),
            "pages_delayed_cta": delayed_ctas,
            "pages_missing_h1": missing_h1s,
        },
        "findings": findings,
        "recommendations": [],
    }

    if referrer_query:
        res["referrer_query"] = referrer_query
        res["evaluations"] = evaluations

    if viewport_only:
        res["viewport_records"] = viewport_records

    return res


def main():
    parser = argparse.ArgumentParser(description="Engagement & Context Continuity Diagnostic Sensor")
    parser.add_argument("--site", "-s", default=None)
    parser.add_argument("--inventory", "-i", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--url", help="Target specific route")
    parser.add_argument("--referrer-query", help="Simulate AI search intent query")
    parser.add_argument("--viewport-only", action="store_true", help="Output viewport answer anchoring records")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

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
    res = audit(
        base,
        domain,
        inv=inv,
        state_file=args.state,
        target_url=args.url,
        referrer_query=args.referrer_query,
        viewport_only=args.viewport_only,
    )
    out = json.dumps(res, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
