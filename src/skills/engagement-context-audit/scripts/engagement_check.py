#!/usr/bin/env python3
"""
engagement_check.py - Engagement & context continuity layer.

Causal Root Causes:
  - EXPERIENCE.CONTINUITY: INTENT_TO_LANDING_MISMATCH, LOW_INFORMATION_SCENT, DESTINATION_NAVIGATION_FRICTION

Evaluates the complete Intent -> Expected Facts -> Landing Page -> Information Scent -> Next Action journey.
Enforces strict Resource Invariant: Only genuine HTML pages enter engagement audits.
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

from fact_extractor import extract_scoped_facts  # type: ignore

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


from safe_fetch import safe_fetch  # type: ignore

KNOWN_LOCALES = {"en", "es", "fr", "de", "it", "jp", "ja", "pt", "nl", "zh", "ko", "ru", "ar"}


def extract_locale_and_path(url):
    parsed = urlparse(url)
    segments = [s for s in parsed.path.strip("/").split("/") if s]
    locale = "default"
    if segments and (segments[0].lower() in KNOWN_LOCALES or re.match(r"^[a-z]{2}(-[a-z]{2})?$", segments[0].lower())):
        locale = segments[0].lower()
        logical_path = "/" + "/".join(segments[1:])
    else:
        logical_path = parsed.path or "/"
    return locale, logical_path


def classify_page(url, title=""):
    """Classify an HTML page with confidence and granular page types."""
    _locale, logical_path = extract_locale_and_path(url)
    segments = [s for s in logical_path.strip("/").split("/") if s]
    t_lower = (title or "").lower()

    if not segments or logical_path == "/":
        return "homepage", "high"
    last_seg = segments[-1]
    if last_seg in ("default", "placeholder", "template", "empty", "sample", "test"):
        return "template", "high"
    if len(segments) == 1 and segments[0] in ("products", "shop", "catalog", "store", "items"):
        return "product_listing", "high"
    if (
        len(segments) >= 2
        and segments[0] in ("products", "p", "product", "item", "items", "shop", "catalog")
        and segments[1] not in ("default", "all", "category", "categories")
    ):
        return "product_detail", "high"
    if any(s in ("category", "categories", "collection", "collections", "browse") for s in segments):
        return "category", "high"
    if any(s in ("subscription", "subscribe", "club", "membership") for s in segments):
        return "subscription_flow", "high"
    if any(s in ("pricing", "prices", "plans", "billing", "pricing-plans") for s in segments):
        return "pricing", "high"
    if any(s in ("contact", "support", "help", "contact-us", "reach-us", "get-in-touch") for s in segments):
        return "contact", "high"
    if any(s in ("location", "locations", "stores", "store-locator", "where-to-buy", "branches") for s in segments):
        return "location", "high"
    if any(s in ("about", "about-us", "company", "our-team", "story", "mission", "who-we-are") for s in segments):
        return "about", "high"
    if any(s in ("docs", "documentation", "guide", "guides", "api", "developer", "manual") for s in segments):
        return "documentation", "high"
    if any(s in ("blog", "news", "article", "articles", "posts", "insights", "journal") for s in segments):
        return "article", "high"
    if re.search(r"\b(contact\s*(us|ez-nous)?|contáctenos|kontakt|お問い合わせ)\b", t_lower):
        return "contact", "high"
    if re.search(r"\b(pricing|plans|tarifs|preise)\b", t_lower):
        return "pricing", "medium"
    if re.search(r"\b(subscription|abonnement|suscripción|subscribe)\b", t_lower):
        return "subscription_flow", "high"
    if re.search(r"\b(products?|catalog|shop|boutique|tienda)\b", t_lower):
        return "product_listing", "medium"
    if re.search(r"\b(about\s*(us)?|notre\s*histoire|sobre\s*nosotros|company)\b", t_lower):
        return "about", "medium"
    return "other", "low"


GENERIC_H1_TERMS = {
    "welcome",
    "home",
    "homepage",
    "untitled",
    "index",
    "hello",
    "welcome to our website",
    "welcome to our site",
    "main page",
    "overview",
}

VALID_CONTACT_TERMS = {
    "contact",
    "contact us",
    "get in touch",
    "reach out",
    "support",
    "contacto",
    "contáctenos",
    "contactez-nous",
    "kontakt",
    "kontaktiere uns",
    "contatti",
    "fale conosco",
    "contato",
    "contate-nos",
    "contacteer ons",
    "kontakt oss",
    "kontakt os",
    "ota yhteyttä",
    "kapcsolat",
    "kontaktujte nás",
    "skontaktuj się z nami",
    "contactati-ne",
    "iletisim",
    "свяжитесь с нами",
    "контакты",
    "اتصل بنا",
    "צור קשר",
    "संपर्क करें",
    "যোগাযোগ করুন",
    "联系我们",
    "聯絡我們",
    "お問い合わせ",
    "문의하기",
    "hubungi kami",
    "liên hệ",
}


class SemanticIntentEngine:
    DEFAULT_INTENTS = {
        "pricing_comparison": {
            "intent_family": "pricing_comparison",
            "required_on_page_facts": ["tier_names", "tier_prices", "billing_interval", "signup_or_trial_cta"],
        },
        "product_purchase": {
            "intent_family": "product_purchase",
            "required_on_page_facts": ["tier_prices", "availability", "add_to_cart_or_buy_cta"],
        },
        "documentation_lookup": {
            "intent_family": "documentation_lookup",
            "required_on_page_facts": ["feature_matrix"],
        },
    }

    def __init__(self, references_dir):
        self.references_dir = references_dir
        self.intents = dict(self.DEFAULT_INTENTS)
        self._load_intents()

    def _load_intents(self):
        if not self.references_dir or not os.path.exists(self.references_dir):
            return
        import glob

        yaml_files = glob.glob(os.path.join(self.references_dir, "*.json"))
        for f in yaml_files:
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    if "intent_family" in data:
                        self.intents[data["intent_family"]] = data
            except Exception:
                pass

    def get_required_facts(self, page_classification):
        if page_classification == "pricing" and "pricing_comparison" in self.intents:
            return self.intents["pricing_comparison"].get("required_on_page_facts", [])
        if page_classification == "product_detail" and "product_purchase" in self.intents:
            return self.intents["product_purchase"].get("required_on_page_facts", [])
        return []

    def check_facts_in_text(self, text, required_facts):
        text_lower = text.lower()
        missing = []
        for fact in required_facts:
            patterns = {
                "tier_names": r"\b(starter|pro|enterprise|basic|premium|free|standard|advanced|tier|plan)\b",
                "billing_interval": r"\b(month|year|annual|mo|yr|monthly|annually)\b",
                "tier_prices": r"(?:\$|€|£|¥|\d+\.\d{2})",
                "feature_matrix": r"\b(feature|compare|include|matrix|custom)\b",
                "signup_or_trial_cta": r"\b(sign up|try|trial|get started|start|subscribe)\b",
                "availability": r"\b(stock|sold out|available|backorder)\b",
                "add_to_cart_or_buy_cta": r"\b(add to cart|buy|purchase|checkout)\b",
            }
            pattern = patterns.get(fact)
            if pattern and not re.search(pattern, text_lower):
                missing.append(fact)
        return missing


COMMERCIAL_ACTION_PATTERNS = re.compile(
    r"\b(buy|order|purchase|checkout|add to cart|subscribe|start free trial|try free|sign up|get started|book demo|contact sales|request demo|get quote)\b",
    re.IGNORECASE,
)

MARKETING_FLUFF_PATTERNS = re.compile(
    r"\b(game-changer|delve|revolutionize|spearhead|testament to|unleash|beacon of|tapestry|multifaceted|cutting-edge|seamless|world-class|next-level)\b",
    re.IGNORECASE,
)


class EngagementDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.title = ""
        self.in_title = False
        self.h1_list = []
        self.h2_list = []
        self.current_tag = None
        self.current_text = []
        self.body_text = []
        self.nav_links = []
        self.nav_link_texts = []
        self.in_anchor = False
        self.current_anchor_text = []
        self.current_href = ""
        self.ctas = []
        self.meta_tags = {}
        self.in_button = False
        self.current_button_text = []
        self.current_is_cta = False
        self.cta_texts = []
        self.in_p = False
        self.current_p_text = []
        self.paragraphs = []
        self.interactive_elements = []

    def handle_starttag(self, tag, attrs):
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
        elif tag_lower == "a":
            self.in_anchor = True
            self.current_anchor_text = []
            self.current_href = attr_dict.get("href", "")
            self.current_is_cta = False
            if self.current_href:
                self.nav_links.append(self.current_href)
                cls = attr_dict.get("class", "").lower()
                role = attr_dict.get("role", "").lower()
                if "btn" in cls or "button" in cls or "cta" in cls or role == "button":
                    self.ctas.append(self.current_href)
                    self.current_is_cta = True

    def handle_endtag(self, tag):
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
        elif tag_lower == "button":
            if self.current_button_text:
                b_text = " ".join(self.current_button_text).strip()
                if b_text:
                    self.cta_texts.append(b_text)
                    is_comm = bool(COMMERCIAL_ACTION_PATTERNS.search(b_text))
                    self.interactive_elements.append(
                        {"tag": "button", "text": b_text, "href": "", "is_commercial_cta": is_comm}
                    )
            self.in_button = False
        elif tag_lower == "a":
            if self.in_anchor and self.current_anchor_text:
                a_text = " ".join(self.current_anchor_text).strip()
                self.nav_link_texts.append(a_text)
                is_comm = bool(COMMERCIAL_ACTION_PATTERNS.search(a_text)) or self.current_is_cta
                self.interactive_elements.append(
                    {"tag": "a", "text": a_text, "href": self.current_href, "is_commercial_cta": is_comm}
                )
                if self.current_is_cta and a_text:
                    self.cta_texts.append(a_text)
            self.in_anchor = False

    def handle_data(self, data):
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


def compute_viewport_answer_anchoring(dom: EngagementDOMParser, full_text: str, page_type: str, facts: dict) -> dict:
    """Evaluate whether arriving visitors from an AI citation find the core answer

    anchored immediately in the top viewport (first 2 paragraphs or first 150 words).
    Addresses post-citation disorientation and bounce.
    """
    lead_paragraphs = dom.paragraphs[:2] if dom.paragraphs else []
    lead_text = " ".join(lead_paragraphs)
    if not lead_text:
        words = full_text.split()
        lead_text = " ".join(words[:150])

    lead_words_count = len(lead_text.split())
    lead_lower = lead_text.lower()
    missing_propositions = []

    anchored = True

    if page_type == "pricing":
        has_price = bool(
            re.search(
                r"(?:\$|€|£|¥|\d+\.\d{2}|\b(?:free|starter|pro|tier|plan|month|annual)\b)",
                lead_lower,
            )
        )
        if not has_price:
            anchored = False
            missing_propositions.append("pricing_figures_or_tiers")

    elif page_type == "product_detail":
        has_function = bool(
            re.search(
                r"\b(?:is|provides|enables|offers|designed for|allows|features|built for)\b",
                lead_lower,
            )
        )
        if not has_function:
            anchored = False
            missing_propositions.append("product_core_functionality")

    elif page_type in ("article", "documentation"):
        has_answer = bool(
            re.search(
                r"\b(?:is|are|means|refers to|defined as|explains|provides)\b",
                lead_lower,
            )
        )
        if not has_answer:
            anchored = False
            missing_propositions.append("direct_answer_definition")

    return {
        "anchored_in_viewport": anchored,
        "lead_words_count": lead_words_count,
        "missing_propositions": missing_propositions,
        "lead_snippet": lead_text[:120],
    }


def compute_cta_reachability_index(dom: EngagementDOMParser) -> dict:
    """Evaluate CTA Reachability Index (CRO / Post-Citation Intent Handoff).

    Measures whether a primary commercial continuation action is available within
    the first 3 interactive elements, or delayed behind excessive auxiliary links.
    """
    elements = dom.interactive_elements
    first_comm_idx = None
    first_comm_text = ""

    for idx, el in enumerate(elements):
        if el.get("is_commercial_cta"):
            first_comm_idx = idx
            first_comm_text = el.get("text", "")
            break

    if first_comm_idx is None:
        return {
            "first_commercial_cta_index": None,
            "preceding_interactive_elements": len(elements),
            "reachability_score": 0.0,
            "is_delayed": True,
            "first_cta_text": "",
        }

    preceding = first_comm_idx
    reachability_score = round(1.0 / (1.0 + preceding), 3)
    is_delayed = preceding > 3

    return {
        "first_commercial_cta_index": first_comm_idx,
        "preceding_interactive_elements": preceding,
        "reachability_score": reachability_score,
        "is_delayed": is_delayed,
        "first_cta_text": first_comm_text,
    }


def compute_information_scent(h1_text: str, lead_text: str) -> dict:
    """Measure information scent purity between H1 and lead content.

    Flags marketing fluff ratio vs substantive value nouns.
    """
    combined = f"{h1_text} {lead_text}".strip()
    words = re.findall(r"\b[a-zA-Z]{3,}\b", combined.lower())
    if not words:
        return {"scent_ratio": 1.0, "fluff_matches": [], "is_diluted": False}

    fluff_found = MARKETING_FLUFF_PATTERNS.findall(combined)
    fluff_count = len(fluff_found)
    fluff_ratio = fluff_count / max(len(words), 1)

    is_diluted = fluff_ratio > 0.03 or fluff_count >= 2
    scent_ratio = round(max(0.0, 1.0 - (fluff_ratio * 10)), 2)

    return {
        "scent_ratio": scent_ratio,
        "fluff_matches": list(set(f.lower() for f in fluff_found)),
        "is_diluted": is_diluted,
    }


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
    avg_sentence_len = round(word_count / sentences, 1)
    is_complex = ari_score > 15.0 or avg_sentence_len > 30.0

    return {
        "ari_score": ari_score,
        "avg_sentence_length": avg_sentence_len,
        "is_complex": is_complex,
    }


GENERIC_H1_TERMS = {"welcome", "home", "main", "untitled", "test", "page", "index", "default"}

WEAK_CTA_PATTERNS = re.compile(
    r"^(submit|click here|learn more|read more|continue|see more|view more|go)$", re.IGNORECASE
)

VALID_CONTACT_TERMS = {
    "contact",
    "contact us",
    "contact-us",
    "contáctenos",
    "contactez-nous",
    "kontakt",
    "contact info",
    "get in touch",
    "reach us",
    "customer service",
    "help desk",
    "support",
    "お問い合わせ",
}


import math
from collections import Counter

# Elite Pre-computed TF-IDF Centroids for Zero-Dependency Semantic Intent Mapping
SITE_TYPE_CENTROIDS = {
    "ecommerce_retail": {
        "shop": 0.5,
        "cart": 0.4,
        "product": 0.3,
        "price": 0.3,
        "shipping": 0.2,
        "return": 0.2,
        "store": 0.2,
        "buy": 0.3,
        "apparel": 0.2,
        "coffee": 0.1,
    },
    "saas_developer": {
        "api": 0.5,
        "docs": 0.4,
        "platform": 0.3,
        "pricing": 0.3,
        "cloud": 0.2,
        "software": 0.2,
        "developer": 0.3,
        "login": 0.2,
        "dashboard": 0.2,
    },
    "media_content": {
        "news": 0.5,
        "article": 0.4,
        "author": 0.3,
        "read": 0.3,
        "publish": 0.2,
        "journal": 0.2,
        "magazine": 0.2,
        "blog": 0.3,
    },
    "service_consulting": {
        "consulting": 0.5,
        "services": 0.4,
        "case": 0.3,
        "study": 0.3,
        "team": 0.2,
        "contact": 0.2,
        "portfolio": 0.3,
        "expertise": 0.2,
    },
}


def cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x] ** 2 for x in vec1])
    sum2 = sum([vec2[x] ** 2 for x in vec2])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    return float(numerator) / denominator if denominator else 0.0


def infer_site_type(html_pages):
    # Semantic Intent Heuristic (Not true ML TF-IDF)
    """
    Semantic Intent Heuristic using Term Frequency
    and Vector Space Cosine Similarity mapping, implemented in pure Python.
    """
    all_text = " ".join((p.get("title", "") + " " + p.get("url", "")) for p in html_pages).lower()
    words = re.findall(r"[a-z]{3,}", all_text)
    if not words:
        return "general_business", ["products", "services", "pricing", "about", "contact", "help"]

    term_counts = Counter(words)
    total_terms = sum(term_counts.values())

    # Calculate Term Frequency (TF) for observed document
    tf_vector = {word: count / total_terms for word, count in term_counts.items()}

    best_match = "general_business"
    best_score = 0.01  # Minimum threshold for confidence

    for category, centroid in SITE_TYPE_CENTROIDS.items():
        score = cosine_similarity(tf_vector, centroid)
        if score > best_score:
            best_score = score
            best_match = category

    # Return destination mapping based on statistical match
    destinations = {
        "ecommerce_retail": ["products", "shop", "catalog", "store", "subscription", "contact", "about"],
        "saas_developer": ["pricing", "features", "docs", "documentation", "api", "contact", "login"],
        "media_content": ["articles", "latest", "topics", "search", "about", "contact"],
        "service_consulting": ["services", "portfolio", "case-studies", "team", "contact", "about"],
    }

    return best_match, destinations.get(best_match, ["products", "services", "pricing", "about", "contact"])


def parse_analytics_data(arg_val, inv=None):
    """
    Parse optional first-party analytics ingestion.
    Supports file path (JSON or CSV), raw JSON string, or dict/list inside inventory.
    Returns: dict mapping normalized path/url -> metrics dict.
    """
    raw_data = None
    if arg_val:
        if isinstance(arg_val, (dict, list)):
            raw_data = arg_val
        elif os.path.exists(str(arg_val)):
            try:
                with open(str(arg_val), "r", encoding="utf-8") as f:
                    content = f.read().strip()
                try:
                    raw_data = json.loads(content)
                except json.JSONDecodeError:
                    import csv
                    import io

                    reader = csv.DictReader(io.StringIO(content))
                    raw_data = list(reader)
            except Exception:
                raw_data = None
        else:
            try:
                raw_data = json.loads(arg_val)
            except Exception:
                raw_data = None
    elif inv and isinstance(inv, dict):
        raw_data = inv.get("analytics")

    if not raw_data:
        return None

    page_metrics_map = {}
    records = []
    if isinstance(raw_data, dict):
        if "pages" in raw_data and isinstance(raw_data["pages"], list):
            records = raw_data["pages"]
        else:
            for k, v in raw_data.items():
                if isinstance(v, dict):
                    v["url"] = v.get("url", k)
                    records.append(v)
    elif isinstance(raw_data, list):
        records = raw_data

    for rec in records:
        if not isinstance(rec, dict):
            continue
        raw_url = rec.get("url", rec.get("path", rec.get("route", "")))
        if not raw_url:
            continue
        parsed = urlparse(raw_url)
        norm_key = parsed.path.rstrip("/").lower() or "/"

        def _to_float(val, is_pct=False):
            if val is None or val == "":
                return None
            if isinstance(val, (int, float)):
                f = float(val)
                return f / 100.0 if (is_pct and f > 1.0) else f
            s = str(val).strip().rstrip("%")
            try:
                f = float(s)
                return f / 100.0 if (is_pct and f > 1.0) else f
            except ValueError:
                return None

        bounce_rate = _to_float(rec.get("bounce_rate", rec.get("bounce")), is_pct=True)
        avg_dwell = _to_float(
            rec.get(
                "avg_time_on_page_seconds",
                rec.get("avg_dwell_time_seconds", rec.get("dwell_time_seconds", rec.get("time_on_page"))),
            )
        )
        scroll_depth = _to_float(rec.get("scroll_depth_pct", rec.get("scroll_depth")), is_pct=False)
        conversion_rate = _to_float(rec.get("conversion_rate", rec.get("cvr")), is_pct=True)
        ai_bounce = _to_float(rec.get("ai_referral_bounce_rate", rec.get("ai_bounce_rate")), is_pct=True)
        organic_bounce = _to_float(
            rec.get("organic_bounce_rate", rec.get("organic_search_bounce_rate")), is_pct=True
        )
        sessions = int(rec.get("sessions", rec.get("pageviews", 0)) or 0)

        entry = {
            "url": raw_url,
            "bounce_rate": bounce_rate,
            "avg_dwell_seconds": avg_dwell,
            "scroll_depth_pct": scroll_depth,
            "conversion_rate": conversion_rate,
            "ai_referral_bounce_rate": ai_bounce,
            "organic_bounce_rate": organic_bounce,
            "sessions": sessions,
        }
        page_metrics_map[norm_key] = entry
        page_metrics_map[raw_url.lower()] = entry

    return page_metrics_map


def audit_page_engagement(html_content, url, page_type="other", state=None):
    state = state or {}
    findings = []
    recommendations = []

    dom = EngagementDOMParser()
    try:
        dom.feed(html_content)
    except Exception as e:
        return (
            [
                {
                    "title": "HTML parsing failed",
                    "severity": "info",
                    "category": "extraction",
                    "root_cause": "Malformed HTML",
                    "evidence": str(e),
                    "suggested_action": {"summary": "Fix HTML syntax", "priority": "low"},
                }
            ],
            [],
            {"visible_words": 0, "h1": False, "navigation_links_found": 0},
        )

    # Build local fact ledger for true semantic evaluation
    facts = extract_scoped_facts(html_content, url)

    nav_text_lower = " ".join(dom.nav_link_texts).lower()

    # 1. Product Pricing Intent Graph
    # Intent: "How much does Product X cost?"
    # Required Facts: Product Entity, Price, Currency
    # Action: Buy, Subscribe, Contact Sales
    if facts.get("scoped_prices"):
        # The page successfully satisfied the information requirement for the pricing intent.
        # Now evaluate continuity: Does it offer the next logical step?
        action_found = any(cta in nav_text_lower for cta in ["buy", "cart", "subscribe", "contact", "order", "get"])
        if not action_found:
            findings.append(
                {
                    "title": "Pricing intent journey lacks explicit commercial continuation",
                    "severity": "medium",
                    "category": "engagement",
                    "cause_family": "EXPERIENCE.CONTINUITY",
                    "id": "INTENT_TO_LANDING_MISMATCH",
                    "cause_id": "INTENT_TO_LANDING_MISMATCH",
                    "root_cause": "The page provides pricing facts for an entity but lacks explicit next-step commercial navigation or transactional actions.",
                    "confidence": "high",
                    "evidence": f"Page {url} provides explicit commercial facts (pricing for '{facts['scoped_prices'][0]['entity']}'), satisfying a bottom-funnel intent, but provides no clear transactional or sales-contact navigation.",
                    "suggested_action": {
                        "summary": "Add explicit CTA (e.g., 'Buy', 'Contact Sales') immediately following the pricing facts to preserve task continuity.",
                        "priority": "medium",
                    },
                }
            )

    # 2. Entity-to-Heading Anchor (Information Scent)
    if not dom.h1_list:
        recommendations.append(
            {
                "title": "Add descriptive H1 heading for visitor orientation",
                "category": "engagement",
                "rationale": f"Page {url} is missing an H1 heading.",
                "summary": "Ensure every page provides a clear <h1> describing its specific value proposition or content.",
                "suggested_action": "Ensure every page provides a clear <h1> describing its specific value proposition or content.",
            }
        )
    elif state and "entities" in state and url in state["entities"]:
        entities = state["entities"][url]
        h1_text = " ".join(dom.h1_list).lower()
        anchor_found = any(ent.lower() in h1_text for ent in entities if len(ent) > 2)
        if entities and not anchor_found:
            findings.append(
                {
                    "category": "engagement",
                    "title": "Broken Information Scent: Entity not anchored in primary heading",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "The page's primary <h1> does not contain the name of the canonical entity, leading to user disorientation upon arrival.",
                    "cause_family": "EXPERIENCE.CONTINUITY",
                    "id": "LOW_INFORMATION_SCENT",
                    "cause_id": "LOW_INFORMATION_SCENT",
                    "evidence": f"Entities {entities} not found in H1 '{dom.h1_list[0]}'.",
                    "suggested_action": {
                        "summary": "Rewrite the <h1> to explicitly include the primary entity name.",
                        "priority": "medium",
                    },
                }
            )

    # 3. Agent UX & Accessibility Barrier (<div onclick> vs semantic buttons)
    div_onclicks = len(re.findall(r"<div\b[^>]*\bonclick\s*=", html_content, re.IGNORECASE))
    if div_onclicks >= 3:
        findings.append(
            {
                "category": "engagement",
                "title": "Interactive elements implemented as non-semantic div-onclick widgets",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "AGENT_INTERACTION_BARRIER: Interactive buttons and CTAs are rendered using <div onclick> rather than semantic <button> or <a> tags.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "id": "AGENT_INTERACTION_BARRIER",
                "cause_id": "AGENT_INTERACTION_BARRIER",
                "evidence": f"Page {url} contains {div_onclicks} non-semantic <div onclick> element(s).",
                "impact": "Autonomous AI agents and browser automation assistants cannot discover, tab through, or trigger non-semantic onclick divs.",
                "suggested_action": {
                    "summary": "Replace <div onclick> elements with native <button> or <a href> tags.",
                    "technical_fix": "Refactor interactive div handlers to semantic HTML5 <button type='button'> or <a href> elements with keyboard focusability.",
                    "creative_fix": "Ensure all call-to-action buttons have accessible, human-readable text labels rather than icon-only divs.",
                    "priority": "medium",
                    "verification": "Confirm grep for '<div[^>]*onclick' returns 0 matches in HTML.",
                },
            }
        )

    # 4. Semantic Landmarks (<main>, <article>, <nav>)
    has_landmarks = bool(re.search(r"<(main|article|nav|aside|header|footer)\b", html_content, re.IGNORECASE))
    if not has_landmarks and len(" ".join(dom.body_text).split()) > 150:
        recommendations.append(
            {
                "id": "PROACTIVE.ENGAGEMENT.SEMANTIC_LANDMARKS.001",
                "title": "Implement HTML5 semantic landmarks (<main>, <article>, <nav>)",
                "category": "engagement",
                "summary": f"Page {url} lacks HTML5 semantic landmarks. AI browsing agents and screen readers use landmarks to orient and extract core content without header/footer noise.",
                "priority": "low",
                "technical_fix": "Wrap primary content in <main> and navigational blocks in <nav>.",
                "creative_fix": "Organize page layout into clear hierarchical sections with distinctive headings.",
                "verification": "Verify HTML contains <main> and <nav> landmarks.",
            }
        )

    # 5. Value-Driven CTA Copy Check (CRO & SXO best practices)
    weak_ctas = [txt for txt in dom.cta_texts if WEAK_CTA_PATTERNS.match(txt.strip())]
    if weak_ctas and len(" ".join(dom.body_text).split()) > 100:
        recommendations.append(
            {
                "id": "PROACTIVE.ENGAGEMENT.VALUE_DRIVEN_CTA.001",
                "title": "Replace generic action-verb CTAs with outcome-oriented value copy",
                "category": "engagement",
                "summary": f"Found generic CTA button/link copy ('{weak_ctas[0]}') on {url}. AI search visitors arrive with high intent; value-driven CTAs ('Start Free Trial', 'See Live Pricing', 'Explore Documentation') preserve context scent and elevate conversion rates.",
                "priority": "low",
                "technical_fix": "Update button and anchor text to state the specific value or asset delivered upon click.",
                "creative_fix": "Adopt the [Action Verb] + [Specific Value] pattern: 'Get Instant Access', 'Compare All Plans', 'Download Integration Guide'.",
                "verification": "Confirm CTA buttons contain descriptive value nouns rather than isolated action verbs.",
            }
        )

    total_body_words = len(" ".join(dom.body_text).split())

    # Deep Post-Citation Engagement Sensors
    viewport_data = compute_viewport_answer_anchoring(dom, " ".join(dom.body_text), page_type, facts)
    cta_data = compute_cta_reachability_index(dom)
    lead_text = " ".join(dom.paragraphs[:2]) if dom.paragraphs else " ".join(dom.body_text[:150])
    h1_str = " ".join(dom.h1_list)
    scent_data = compute_information_scent(h1_str, lead_text)
    readability_data = compute_cognitive_readability(lead_text)

    # 1.1 Viewport Answer Anchoring Check (Post-Citation Orientation Shock)
    if (
        page_type in ("pricing", "product_detail", "article", "documentation")
        and total_body_words >= 120
        and not viewport_data["anchored_in_viewport"]
    ):
        findings.append(
            {
                "category": "engagement",
                "title": "Cited proposition missing from early-content document section (Orientation Shock)",
                "severity": "medium",
                "confidence": "high",
                "root_cause": (
                    "VIEWPORT_ANSWER_ABSENCE: The early-content section (first 150 words / top 2 paragraphs) fails to anchor "
                    f"the core proposition ({', '.join(viewport_data['missing_propositions'])}). AI search visitors arriving from citations "
                    "experience orientation shock when the cited fact is delayed behind boilerplate banners."
                ),
                "cause_family": "EXPERIENCE.CONTINUITY",
                "id": "VIEWPORT_ANSWER_ABSENCE",
                "cause_id": "VIEWPORT_ANSWER_ABSENCE",
                "evidence": f"Page {url} ({page_type}) lacks immediate proposition anchoring in its lead {viewport_data['lead_words_count']} words.",
                "suggested_action": {
                    "summary": "Anchor the core product proposition, pricing figures, or direct answer in the lead 60 words.",
                    "technical_fix": "Insert an early-content answer summary box directly beneath the H1 before auxiliary navigation blocks.",
                    "creative_fix": "Adopt the Direct Answer Inversion format: state the primary resolution immediately in paragraph 1.",
                    "priority": "high" if page_type == "pricing" else "medium",
                    "verification": "Confirm lead 100 words contain explicit entity prices or core definitions.",
                },
            }
        )

    # 1.2 CTA Reachability Index (CRO / Transactional Continuation)
    if page_type in ("product_detail", "pricing", "subscription_flow") and cta_data["is_delayed"]:
        findings.append(
            {
                "category": "engagement",
                "title": "Commercial continuation CTA delayed behind auxiliary interactive elements",
                "severity": "medium",
                "confidence": "high",
                "root_cause": (
                    f"CTA_REACHABILITY_FRICTION: The first commercial continuation action is preceded by "
                    f"{cta_data['preceding_interactive_elements']} auxiliary interactive elements (Reachability Index: {cta_data['reachability_score']:.2f}). "
                    "High-intent citation traffic arriving from AI search bounces when the primary transactional next-step is buried beneath header navigation."
                ),
                "cause_family": "EXPERIENCE.CONTINUITY",
                "id": "CTA_REACHABILITY_FRICTION",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "evidence": f"Page {url} ({page_type}) places its first commercial CTA at position #{cta_data['first_commercial_cta_index'] + 1 if cta_data['first_commercial_cta_index'] is not None else 'N/A'}.",
                "suggested_action": {
                    "summary": "Position a prominent commercial continuation CTA within the first 3 interactive elements on the page.",
                    "technical_fix": "Place a prominent primary action button ('Buy', 'Start Free Trial', 'Contact Sales') directly in the early-content hero section.",
                    "creative_fix": "Pair the primary value proposition with an instant action trigger to eliminate navigational friction.",
                    "priority": "medium",
                    "verification": "Confirm commercial CTA appears within the first 3 interactive DOM elements.",
                },
            }
        )

    # 1.3 Information Scent Purity
    if scent_data["is_diluted"] and total_body_words >= 100:
        recommendations.append(
            {
                "id": "PROACTIVE.ENGAGEMENT.INFORMATION_SCENT_PURITY.001",
                "title": "Replace buzzword marketing fluff with substantive domain nouns in lead copy",
                "category": "engagement",
                "summary": (
                    f"Lead content on {url} exhibits diluted information scent (detected promotional terms: {', '.join(scent_data['fluff_matches'])}). "
                    "Visitors arriving from AI citations seek immediate confirmation of technical attributes and commercial details; subjective marketing fluff elevates bounce rates."
                ),
                "priority": "low",
                "technical_fix": "Purge promotional descriptors and replace with specific feature names, specifications, and verified capabilities.",
                "creative_fix": "Adopt crisp, informative prose that directly fulfills the promise of the page title and citation snippet.",
                "verification": "Confirm fluff ratio is under 3% of lead text tokens.",
            }
        )

    # 1.4 Cognitive Simplicity / Readability
    if readability_data["is_complex"] and total_body_words >= 100:
        recommendations.append(
            {
                "id": "PROACTIVE.ENGAGEMENT.COGNITIVE_SIMPLICITY.001",
                "title": "Streamline sentence structure in lead copy to lower cognitive friction",
                "category": "engagement",
                "summary": (
                    f"Lead paragraph on {url} has an elevated reading complexity score (ARI: {readability_data['ari_score']}, avg sentence: {readability_data['avg_sentence_length']} words). "
                    "Arriving AI referral visitors skim for immediate answers; high sentence complexity increases abandonment."
                ),
                "priority": "low",
                "technical_fix": "Break long compound sentences (exceeding 25 words) into concise declarative statements.",
                "creative_fix": "Use the 15-20 word sentence standard for introductory explanations and value propositions.",
                "verification": "Confirm average sentence length in opening paragraphs is <= 22 words.",
            }
        )

    return (
        findings,
        recommendations,
        {
            "visible_words": total_body_words,
            "h1": len(dom.h1_list) > 0,
            "navigation_links_found": len(dom.nav_links),
            "anchor_links_found": len(dom.nav_links),
            "cta_reachability_score": cta_data["reachability_score"],
            "viewport_anchored": viewport_data["anchored_in_viewport"],
            "information_scent_score": scent_data["scent_ratio"],
            "ari_readability_score": readability_data["ari_score"],
        },
    )


def audit(base, domain, inv=None, state_file=None, analytics=None):
    if state_file and os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                json.load(f)
        except Exception:
            pass
    findings = []
    recommendations = []
    observations = []
    page_metrics = []

    analytics_map = parse_analytics_data(analytics, inv=inv)

    html_pages = []
    if inv is not None:
        for p in inv.get("pages", []):
            u = p.get("url") or ""
            raw_html = p.get("html") or ""
            if not u or not raw_html:
                continue
            if u.lower().endswith((".xml", ".xml.gz", ".txt", ".json", ".pdf")):
                continue
            if (
                raw_html.strip().startswith("<?xml")
                or "<urlset" in raw_html.lower()
                or "<sitemapindex" in raw_html.lower()
            ):
                continue
            html_pages.append(p)
    else:
        _status, html, _, _ = safe_fetch(base + "/", timeout=10, max_bytes=2 * 1024 * 1024)
        if html:
            html_pages.append({"url": base + "/", "html": html, "page_type": "homepage"})

    site_type = infer_site_type(html_pages)[0]

    corroborated_findings_count = 0
    mitigated_findings_count = 0
    pages_with_analytics = 0
    observed_bounces: list[float] = []
    observed_dwells: list[float] = []

    for p in html_pages:
        p_findings, p_recs, p_data = audit_page_engagement(
            p["html"],
            p["url"],
            page_type=p.get("page_type", "other"),
        )

        p_url = p.get("url", "")
        path_key = urlparse(p_url).path.rstrip("/").lower() or "/"
        p_analytics = None
        if analytics_map:
            p_analytics = analytics_map.get(p_url.lower()) or analytics_map.get(path_key)

        if p_analytics:
            pages_with_analytics += 1
            b_rate = p_analytics.get("bounce_rate")
            d_time = p_analytics.get("avg_dwell_seconds")
            ai_bounce = p_analytics.get("ai_referral_bounce_rate")
            org_bounce = p_analytics.get("organic_bounce_rate")

            if b_rate is not None:
                observed_bounces.append(b_rate)
            if d_time is not None:
                observed_dwells.append(d_time)

            # 1. Empirical Corroboration of Static Findings
            if b_rate is not None and (b_rate >= 0.60 or (d_time is not None and d_time <= 20)):
                for f in p_findings:
                    if f.get("category") == "engagement":
                        f["confidence"] = "high"
                        f["severity"] = "high"
                        f["evidence"] = (
                            f"{f.get('evidence', '')} [Empirically Corroborated: First-party analytics records "
                            f"{b_rate * 100:.1f}% bounce rate and {d_time or 'N/A'}s dwell time, providing behavioral evidence consistent with visitor drop-off.]"
                        )
                        corroborated_findings_count += 1

            # 2. Heuristic Mitigation (Observed Retention is Healthy)
            elif b_rate is not None and b_rate <= 0.35 and (d_time is not None and d_time >= 60):
                for f in p_findings:
                    if f.get("category") == "engagement":
                        f["severity"] = "low"
                        f["evidence"] = (
                            f"{f.get('evidence', '')} [Mitigated by Analytics: Observed visitor retention is healthy "
                            f"({b_rate * 100:.1f}% bounce, {d_time}s dwell); static heuristic warning is lowered in priority.]"
                        )
                        mitigated_findings_count += 1

            # 3. AI Referral Discontinuity (Citation expectation mismatch)
            if ai_bounce is not None:
                baseline_bounce = org_bounce if org_bounce is not None else 0.40
                if ai_bounce - baseline_bounce >= 0.25:
                    p_findings.append(
                        {
                            "title": f"AI search referral bounce rate severely diverges from organic baseline ({p_url})",
                            "severity": "high",
                            "category": "engagement",
                            "cause_family": "EXPERIENCE.CONTINUITY",
                            "id": "AI_REFERRAL_DISCONTINUITY",
                            "cause_id": "AI_REFERRAL_DISCONTINUITY",
                            "confidence": "high",
                            "root_cause": (
                                f"Observed AI referral traffic exhibits a {ai_bounce * 100:.1f}% bounce rate compared to a "
                                f"{baseline_bounce * 100:.1f}% organic search baseline. Visitors referred from generative AI answers "
                                f"experience post-citation orientation friction when cited answers are not instantly visible in early content."
                            ),
                            "evidence": (
                                f"First-party analytics for {p_url} reveals AI referral bounce rate of {ai_bounce * 100:.1f}% "
                                f"versus {baseline_bounce * 100:.1f}% organic baseline (+{(ai_bounce - baseline_bounce) * 100:.1f}% gap)."
                            ),
                            "suggested_action": {
                                "summary": "Anchor cited AI query propositions in the early-content document section and place prominent continuation CTA.",
                                "priority": "high",
                                "technical_fix": "Add an early-content callout box verifying the specific product/service claims cited by AI assistants.",
                                "creative_fix": "Align hero H1 and introductory sentence directly with the citation query intent.",
                                "verification": "Monitor AI referral cohort bounce rate over 14 days post-remediation.",
                            },
                        }
                    )

        findings.extend(p_findings)
        recommendations.extend(p_recs)
        page_metrics.append(p_data)

    # 6. AI Buying Agent Readiness: Machine-Readable Pricing Manifest (/pricing.md)
    pricing_present = False
    if inv is not None:
        pricing_info = inv.get("infrastructure", {}).get("pricing_manifest")
        if pricing_info and isinstance(pricing_info, dict):
            pricing_present = pricing_info.get("present", False)
    else:
        status_pm, p_body, _, _ = safe_fetch(f"{base}/pricing.md", timeout=5, max_bytes=512 * 1024)
        if status_pm == 200 and bool(p_body):
            pricing_present = True
        else:
            status_pt, pt_body, _, _ = safe_fetch(f"{base}/pricing.txt", timeout=5, max_bytes=512 * 1024)
            pricing_present = status_pt == 200 and bool(pt_body)

    if pricing_present:
        observations.append(
            {
                "observation": "Found machine-readable /pricing.md manifest for AI buying agents.",
                "impact": "Autonomous procurement and shopping agents can evaluate plan tiers programmatically.",
                "role": "purchasing",
            }
        )
    else:
        recommendations.append(
            {
                "id": "PROACTIVE.ENGAGEMENT.AGENT_PRICING_MANIFEST.001",
                "title": "Publish a machine-readable /pricing.md manifest for AI buying agents",
                "category": "engagement",
                "summary": "The site does not publish a machine-readable /pricing.md or /pricing.txt manifest. Autonomous AI purchasing agents (OpenAI Operator, Google Project Mariner) evaluate tools and services programmatically before human buyers visit.",
                "priority": "low",
                "technical_fix": "Publish a structured /pricing.md file at the domain root with tier names, price limits, and feature bullets.",
                "creative_fix": "Include transparent plan thresholds and billing cadences without contact-sales gates.",
                "verification": f"Confirm {base}/pricing.md returns HTTP 200 with text/markdown.",
            }
        )

    if not page_metrics:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve HTML content from {base}",
        }

    mode = "analytics_augmented" if analytics_map else "heuristic_only"
    avg_bounce = round(sum(observed_bounces) / len(observed_bounces), 3) if observed_bounces else None
    avg_dwell = round(sum(observed_dwells) / len(observed_dwells), 1) if observed_dwells else None

    analytics_summary = {
        "mode": mode,
        "first_party_analytics_provided": bool(analytics_map),
        "pages_with_analytics": pages_with_analytics,
        "average_observed_bounce_rate": avg_bounce,
        "average_observed_dwell_seconds": avg_dwell,
        "corroborated_findings_count": corroborated_findings_count,
        "mitigated_findings_count": mitigated_findings_count,
    }

    limitations = [
        "Engagement and orientation analysis is based on static HTML layout semantics; dynamic client-rendered overlays were not evaluated."
    ]
    if mode == "heuristic_only":
        limitations.append(
            "Engagement evaluation operated in heuristic-only mode based on static HTML layout proxies (heading hierarchy, CTA placement, information scent). First-party behavioral analytics (bounce rates, dwell times, scroll depths, AI-referral cohort drop-offs) were not provided. Static proxies indicate structural risks, not observed visitor drop-off."
        )

    engagement_continuity_summary = {
        "mode": mode,
        "pages_audited": len(page_metrics),
        "pages_with_viewport_anchoring": sum(1 for pm in page_metrics if pm.get("viewport_anchored", False)),
        "average_cta_reachability_score": round(
            sum(pm.get("cta_reachability_score", 0.0) for pm in page_metrics) / max(1, len(page_metrics)), 2
        ),
        "average_information_scent_score": round(
            sum(pm.get("information_scent_score", 1.0) for pm in page_metrics) / max(1, len(page_metrics)), 2
        ),
    }

    return {
        "status": "ok",
        "engagement_mode": mode,
        "analytics_summary": analytics_summary,
        "engagement_continuity_summary": engagement_continuity_summary,
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "html_pages_evaluated": len(html_pages),
            "site_type_inferred": site_type,
            "average_visible_words": round(
                sum(pm["visible_words"] for pm in page_metrics) / max(1, len(page_metrics)), 1
            ),
            "pages_with_h1": sum(1 for pm in page_metrics if pm["h1"]),
            "pages_with_navigation": sum(
                1 for pm in page_metrics if pm.get("navigation_links_found", pm.get("anchor_links_found", 0)) > 0
            ),
            "pages_with_analytics": pages_with_analytics,
            # Continuous scoring: orientation & intent-handoff ratios
            "h1_aligned_pages": sum(
                1 for pm in page_metrics
                if pm["h1"] and pm.get("information_scent_score", 0.0) >= 0.4
            ),
            "cta_above_fold_pages": sum(
                1 for pm in page_metrics
                if pm.get("cta_reachability_score", 0.0) > 0.0
            ),
            "total_pages": len(page_metrics),
        },
        "limitations": limitations,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Audit on-site visitor orientation, heading hierarchies, and navigation."
    )
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
    parser.add_argument("--state", help="Path to global state JSON")
    parser.add_argument(
        "--analytics",
        help="Path to first-party analytics JSON/CSV file or JSON string",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    args = parser.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    res = audit(base, p.netloc, inv=inv, state_file=args.state, analytics=args.analytics)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
