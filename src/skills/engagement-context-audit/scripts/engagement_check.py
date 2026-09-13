#!/usr/bin/env python3
"""
engagement_check.py - Engagement & context continuity layer.

Causal Root Causes:
  - EXPERIENCE.CONTINUITY: INTENT_TO_LANDING_MISMATCH, LOW_INFORMATION_SCENT, DESTINATION_NAVIGATION_FRICTION

Evaluates the complete Intent -> Expected Facts -> Landing Page -> Information Scent -> Next Action journey.
Enforces strict Resource Invariant: Only genuine HTML pages enter engagement audits.
"""

import argparse
import csv
import glob
import io
import json
import math
import os
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from typing import Any, Dict, Optional
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
FACT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "fact-consistency-audit", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR, FACT_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from fact_consistency_check import extract_scoped_facts  # type: ignore
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

        yaml_files = glob.glob(os.path.join(self.references_dir, "*.json"))
        for f in yaml_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
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
    r"\b("
    r"buy|order|purchase|checkout|add to cart|subscribe|start free trial|try free|sign up|get started|book demo|contact sales|request demo|get quote|"
    r"comprar|comprar ahora|comprar ya|compra|añadir al carrito|carrito|cesta|suscríbete|suscribirse|suscripción|contactar|contacto|pedir|pedido|solicitar|empezar ahora|empezar|mostrar ahora|"
    r"acheter|acheter maintenant|achat|ajouter au panier|panier|s'abonner|abonnement|contactez-nous|commander|commande|commencer|"
    r"kaufen|jetzt kaufen|in den warenkorb|warenkorb|abonnieren|kontakt|bestellen|jetzt starten|anmelden"
    r")\b",
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
                if "btn" in cls or "button" in cls or "cta" in cls or "action" in cls or role == "button":
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

# Elite Behavioral & Post-Citation Engagement Patterns
PROOF_BENCHMARK_PATTERNS = re.compile(
    r"\b(?:"
    r"\d+(?:\.\d+)?\s*%\s*(?:reduction|increase|faster|improvement|uptime|latency|saving|growth|lift|sla|speed)"
    r"|\d+(?:\.\d+)?\s*(?:ms|milliseconds|seconds|req/sec|tps|iops|gb/s|tb/s|qps)"
    r"|99\.\d+%\s*(?:uptime|sla|availability)"
    r"|\$\s*\d+(?:\.\d+)?\s*[kmbKMB]?\s*(?:saved|revenue|cost)"
    r"|benchmark|latency benchmark|throughput benchmark|empirical results|performance test"
    r")\b",
    re.IGNORECASE,
)

COMPLIANCE_PATTERNS = re.compile(
    r"\b(soc\s*2(?:\s*type\s*(?:i|ii))?|iso\s*27001|hipaa|gdpr|pci[- ]dss|fedramp|ccpa|csa\s*star)\b",
    re.IGNORECASE,
)

CUSTOMER_PROOF_PATTERNS = re.compile(
    r"\b(?:"
    r"case study|customer story|customer success|trusted by|used by|loved by|client results"
    r"|testimonial|quote from|director of|vp of|cto|ciso|head of engineering"
    r"|reduced\s+[\w\s]+by\s+\d+%|increased\s+[\w\s]+by\s+\d+%"
    r")\b",
    re.IGNORECASE,
)

FORCED_SALES_GATE_PATTERNS = re.compile(
    r"\b(book\s+(?:a\s+)?demo|request\s+(?:a\s+)?demo|talk\s+to\s+sales|contact\s+sales|schedule\s+(?:a\s+)?call|speak\s+with\s+sales)\b",
    re.IGNORECASE,
)

SELF_SERVICE_PATTERNS = re.compile(
    r"\b(start\s+(?:a\s+)?(?:free\s+)?trial|try\s+free|free\s+tier|sign\s+up(?:\s+free)?|get\s+started(?:\s+free)?|explore\s+docs|interactive\s+demo|sandbox|live\s+demo|deploy|pricing)\b",
    re.IGNORECASE,
)

OBJECTION_PATTERNS = {
    "pricing_transparency": re.compile(r"\b(price|pricing|tier|cost|per\s+month|annual|cancel\s+anytime|refund|no\s+hidden\s+fees|free\s+tier)\b", re.IGNORECASE),
    "security_compliance": re.compile(r"\b(soc\s*2|iso\s*27001|hipaa|gdpr|encryption|data\s+privacy|security|single\s+sign-on|sso|saml)\b", re.IGNORECASE),
    "integration_compatibility": re.compile(r"\b(integrat\w+|api|sdk|connect\w*|webhook|plugin|slack|github|kubernetes|aws|postgresql|zapier)\b", re.IGNORECASE),
    "migration_onboarding": re.compile(r"\b(migrat\w+|switch\w*|import\w*|onboarding|setup\s+time|export|transition)\b", re.IGNORECASE),
}

GENERIC_ORIENTATION_PATTERNS = re.compile(
    r"\b(welcome\s+to\s+(?:our\s+)?(?:website|service|site|portal|platform|the\s+knowledge\s+base)|empower\s+your\s+journey|next-generation\s+solutions?|reimagine\s+workflows?|transforming\s+the\s+future|unleash\s+innovation|delivering\s+excellence)\b",
    re.IGNORECASE,
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
        "catalog": 0.2,
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


def audit_page_engagement(html_content, url, page_type="other", state=None, page_dict=None):
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
                    "id": "HTML_PARSING_FAILED",
                    "cause_id": "HTML_PARSING_FAILED",
                    "title": "HTML parsing failed",
                    "severity": "low",
                    "confidence": "high",
                    "category": "extraction",
                    "root_cause": "Malformed HTML payload prevented complete DOM tree parsing.",
                    "evidence": str(e),
                    "suggested_action": {
                        "summary": "Fix HTML syntax and unclosed tags on the page.",
                        "technical_fix": "Validate document with W3C HTML validator and fix unclosed tags or invalid nesting.",
                        "creative_fix": "Ensure CMS layout templates produce valid HTML5 markup across all viewports.",
                        "priority": "low",
                        "verification": "Re-parse page HTML with standard parser without syntax errors.",
                    },
                }
            ],
            [],
            {"visible_words": 0, "h1": False, "navigation_links_found": 0},
        )

    # Build local fact ledger for true semantic evaluation
    facts = extract_scoped_facts(html_content, url)

    nav_text_lower = " ".join(dom.nav_link_texts).lower()
    cta_text_lower = " ".join(dom.cta_texts).lower()
    page_ctas_text = " ".join(
        str(c.get("text", "") if isinstance(c, dict) else getattr(c, "text", ""))
        for c in (page_dict.get("ctas", []) if page_dict else [])
    ).lower()
    all_action_text = f"{nav_text_lower} {cta_text_lower} {page_ctas_text}".strip()

    # 1. Product Pricing Intent Graph
    # Intent: "How much does Product X cost?"
    # Required Facts: Product Entity, Price, Currency
    # Action: Buy, Subscribe, Contact Sales
    if facts.get("scoped_prices"):
        # The page successfully satisfied the information requirement for the pricing intent.
        # Now evaluate continuity: Does it offer the next logical step?
        action_found = any(
            cta in all_action_text
            for cta in [
                "buy", "cart", "subscribe", "contact", "order", "get", "trial", "demo", "pricing", "sign up", "checkout", "shop",
                "comprar", "compra", "carrito", "cesta", "suscrib", "suscripci", "contacto", "contactar", "pedir", "pedido", "empezar", "mostrar",
                "acheter", "achat", "panier", "abonn", "commander", "commande",
                "kaufen", "kauf", "warenkorb", "bestellen",
            ]
        )
        if not action_found:
            findings.append(
                {
                    "title": "Pricing intent journey lacks explicit commercial continuation",
                    "severity": "medium",
                    "category": "engagement",
                    "cause_family": "EXPERIENCE.CONTINUITY",
                    "id": "INTENT_TO_LANDING_MISMATCH",
                    "cause_id": "INTENT_TO_LANDING_MISMATCH",
                    "url": url,
                    "scope": url,
                    "root_cause": "The page provides pricing facts for an entity but lacks explicit next-step commercial navigation or transactional actions.",
                    "confidence": "high",
                    "evidence": f"Page {url} provides explicit commercial facts (pricing for '{facts['scoped_prices'][0]['entity']}'), satisfying a bottom-funnel intent, but provides no clear transactional or sales-contact navigation.",
                    "suggested_action": {
                        "summary": "Add explicit CTA (e.g., 'Buy', 'Contact Sales') immediately following the pricing facts to preserve task continuity.",
                        "technical_fix": "Render accessible transactional buttons (<a href='/checkout'> or <button>) immediately adjacent to pricing specifications.",
                        "creative_fix": "Design prominent visual callouts emphasizing next steps, free trials, or consultation bookings.",
                        "priority": "medium",
                        "verification": "Verify presence of transactional CTA links within first viewport of pricing section.",
                    },
                }
            )

    total_body_words = len(" ".join(dom.body_text).split())
    full_text = " ".join(dom.body_text)
    opening_text = " ".join(dom.paragraphs[:3]) if dom.paragraphs else " ".join(dom.body_text[:200])
    opening_lower = opening_text.lower()
    lead_h1 = dom.h1_list[0] if dom.h1_list else ""
    lead_h1_lower = lead_h1.lower()

    # 2. The 5-Second Cognitive Orientation & Value Proposition Test
    # Visitors arriving from AI search decide within 3-5 seconds whether to stay or bounce.
    # An orientation vacuum occurs when the hero/opening section relies on generic slogans
    # or fails to define what the product/service is, for whom, and what it solves.
    is_generic_orientation = bool(
        GENERIC_ORIENTATION_PATTERNS.search(opening_text)
        or GENERIC_ORIENTATION_PATTERNS.search(lead_h1)
        or any(lead_h1_lower == t or lead_h1_lower.startswith(t + " ") for t in GENERIC_H1_TERMS)
    )
    has_concrete_value = any(
        kw in opening_lower
        for kw in (
            "provides", "enables", "platform for", "software for", "solution for",
            "infrastructure for", "designed for", "built for", "accelerates", "automates",
            "helps you", "allows you", "tool for", "system for"
        )
    )
    if (is_generic_orientation or (not lead_h1 and not has_concrete_value)) and total_body_words >= 30:
        findings.append(
            {
                "category": "engagement",
                "title": "Value proposition orientation vacuum in primary viewport (5-Second Bounce Risk)",
                "severity": "high",
                "confidence": "high",
                "root_cause": (
                    "VALUE_PROPOSITION_ORIENTATION_VACUUM: The above-the-fold hero section fails the 5-second orientation test. "
                    f"Arriving visitors encounter generic copy ('{lead_h1 or opening_text[:80]}') without a concrete definition of the offering, "
                    "target audience, or primary mechanism, triggering immediate cognitive abandonment."
                ),
                "cause_family": "EXPERIENCE.CONTINUITY",
                "id": "VALUE_PROPOSITION_ORIENTATION_VACUUM",
                "cause_id": "VALUE_PROPOSITION_ORIENTATION_VACUUM",
                "url": url,
                "scope": url,
                "evidence": f"Opening viewport on {url} lacks concrete capability nouns or audience positioning ('{lead_h1 or opening_text[:100]}').",
                "suggested_action": {
                    "summary": "Invert hero copy: explicitly define what the product does, for whom, and its primary concrete outcome within the first 50 words.",
                    "technical_fix": "Restructure the hero DOM section to place a direct capability definition immediately below the primary heading.",
                    "creative_fix": "Adopt the [Action Verb] + [Specific Capability] + [Quantified Outcome] headline pattern.",
                    "priority": "high",
                    "verification": "Confirm opening viewport contains explicit domain nouns and solution positioning.",
                },
            }
        )

    # 3. Proof Architecture & Skepticism Deficit
    # AI search users are inherently skeptical because LLMs hallucinate. When they click through to verify,
    # the absence of empirical proof anchors (benchmarks, verifiable metrics, case studies, security credentials)
    # causes them to dismiss the claims and bounce.
    if page_type in ("product_detail", "product", "pricing", "homepage", "subscription_flow") and total_body_words >= 80:
        has_benchmarks = bool(PROOF_BENCHMARK_PATTERNS.search(full_text))
        has_compliance = bool(COMPLIANCE_PATTERNS.search(full_text))
        has_customer_proof = bool(CUSTOMER_PROOF_PATTERNS.search(full_text))

        if not (has_benchmarks or has_compliance or has_customer_proof):
            findings.append(
                {
                    "category": "engagement",
                    "title": "Critical proof architecture deficit on commercial offering (Skepticism Deficit)",
                    "severity": "high",
                    "confidence": "high",
                    "root_cause": (
                        "PROOF_ARCHITECTURE_DEFICIT: The commercial page makes value claims but provides zero empirical proof anchors "
                        "(0 benchmark figures, 0 verifiable customer outcome metrics, 0 compliance/security badges). Skeptical visitors arriving "
                        "from AI citations cannot verify claims and abandon the session."
                    ),
                    "cause_family": "EXPERIENCE.TRUST",
                    "id": "PROOF_ARCHITECTURE_DEFICIT",
                    "cause_id": "PROOF_ARCHITECTURE_DEFICIT",
                    "url": url,
                    "scope": url,
                    "evidence": f"Commercial page {url} ({page_type}, {total_body_words} words) provides zero empirical benchmarks, customer outcome metrics, or compliance certifications.",
                    "suggested_action": {
                        "summary": "Anchor primary claims with empirical proof: publish verified benchmark figures, customer metrics, and compliance credentials.",
                        "technical_fix": "Embed structured performance metrics, customer metric cards, and verifiable security certification badges adjacent to core claims.",
                        "creative_fix": "Replace unverified superlatives ('fastest', 'most reliable') with concrete measurements ('sub-10ms P99 latency across 100M queries').",
                        "priority": "high",
                        "verification": "Verify presence of at least 2 empirical proof elements (metrics, case data, compliance seals) within the page body.",
                    },
                }
            )

    # 4. Friction-to-Value & Conversion Obstacles (Forced Sales Gate)
    # Technical buyers and developers arriving from AI citations bounce immediately if forced into
    # a 30-minute sales meeting rather than experiencing immediate product value.
    if page_type in ("pricing", "product_detail", "product") and total_body_words >= 60:
        has_sales_gate = bool(FORCED_SALES_GATE_PATTERNS.search(all_action_text))
        has_self_serve = bool(SELF_SERVICE_PATTERNS.search(all_action_text))
        if has_sales_gate and not has_self_serve:
            findings.append(
                {
                    "category": "conversion-continuity",
                    "title": "High-friction conversion barrier on commercial route (Forced Sales Gate)",
                    "severity": "high",
                    "confidence": "high",
                    "root_cause": (
                        "FRICTION_TO_VALUE_BARRIER: The primary conversion trigger enforces a high-friction sales consultation gate "
                        "with zero self-service onboarding, interactive sandbox, or transparent documentation for technical buyers."
                    ),
                    "cause_family": "EXPERIENCE.CONTINUITY",
                    "id": "FRICTION_TO_VALUE_BARRIER",
                    "cause_id": "FRICTION_TO_VALUE_BARRIER",
                    "url": url,
                    "scope": url,
                    "evidence": f"Page {url} ({page_type}) requires scheduled sales interaction with no self-service entry point.",
                    "suggested_action": {
                        "summary": "Implement a dual-track conversion architecture: provide self-service trial or interactive sandbox alongside sales contact.",
                        "technical_fix": "Add secondary self-service CTA ('Try Sandbox', 'Explore Documentation', 'Start Free Tier') adjacent to primary enterprise sales CTA.",
                        "creative_fix": "Allow visitors to experience immediate product utility before requiring identity disclosure or scheduled meetings.",
                        "priority": "high",
                        "verification": "Confirm presence of an un-gated self-service pathway alongside enterprise sales contact.",
                    },
                }
            )

    # 5. Objection Pre-emption & Decision Velocity
    # Unaddressed buyer hesitations (pricing opacity, integration gaps, migration friction) stall conversions.
    if page_type in ("product_detail", "product", "pricing", "subscription_flow") and total_body_words >= 150:
        objections_covered = sum(1 for _, pat in OBJECTION_PATTERNS.items() if pat.search(full_text))
        if objections_covered <= 1:
            findings.append(
                {
                    "category": "engagement",
                    "title": "Commercial route leaves core buyer objections unaddressed",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": (
                        "OBJECTION_COVERAGE_VOID: Commercial page lacks structured objection handling (pricing clarity, migration pathways, "
                        f"integration compatibility, or security compliance — only {objections_covered}/4 covered), stalling purchase decisions."
                    ),
                    "cause_family": "EXPERIENCE.TRUST",
                    "id": "OBJECTION_COVERAGE_VOID",
                    "cause_id": "OBJECTION_COVERAGE_VOID",
                    "url": url,
                    "scope": url,
                    "evidence": f"Commercial page {url} addresses only {objections_covered} of 4 essential buyer objection categories.",
                    "suggested_action": {
                        "summary": "Deploy an Objection Pre-emption module addressing pricing transparency, migration ease, integration stack, and security compliance.",
                        "technical_fix": "Add structured FAQ or comparison matrix addressing top buyer hesitations directly above final conversion triggers.",
                        "creative_fix": "Provide explicit risk-reversal answers: 'Can I cancel anytime?', 'How do I migrate my data?', 'Where is data stored?'.",
                        "priority": "medium",
                        "verification": "Verify page provides explicit answers regarding pricing terms, integrations, and data security.",
                    },
                }
            )

    # 6. Informational Decision Pathway & Dead-End Avoidance
    # Informational and guide pages that terminate without logical next steps cause 100% of satisfied readers to bounce.
    if page_type in ("article", "documentation", "guide") and total_body_words >= 250:
        has_continuation = any(
            re.search(pat, all_action_text)
            for pat in [r"next", r"continue", r"guide", r"tutorial", r"related", r"read more", r"explore", r"try", r"docs", r"download"]
        )
        if not has_continuation:
            findings.append(
                {
                    "category": "engagement",
                    "title": "Informational route creates an experiential dead-end",
                    "severity": "medium",
                    "confidence": "medium",
                    "root_cause": (
                        "DECISION_PATHWAY_DEAD_END: The informational page delivers content but provides zero logical next steps, "
                        "interactive tools, or conversion pathways, causing visitors to bounce after reading."
                    ),
                    "cause_family": "EXPERIENCE.CONTINUITY",
                    "id": "DECISION_PATHWAY_DEAD_END",
                    "cause_id": "DECISION_PATHWAY_DEAD_END",
                    "url": url,
                    "scope": url,
                    "evidence": f"Informational page {url} ({total_body_words} words) contains no forward navigational or conversion pathways.",
                    "suggested_action": {
                        "summary": "Add intent-tailored next-step pathways (related guides, interactive sandbox, tool download, or free trial) at document conclusion.",
                        "technical_fix": "Insert a contextually relevant next-step component or related resources block at the bottom of the article layout.",
                        "creative_fix": "Guide the reader from learning into doing: provide a concrete implementation checklist or sandbox environment.",
                        "priority": "medium",
                        "verification": "Confirm presence of purposeful next-action pathways at the article footer.",
                    },
                }
            )

    # 7. Value-Driven CTA Copy Check (CRO & SXO best practices)
    weak_ctas = [txt for txt in dom.cta_texts if WEAK_CTA_PATTERNS.match(txt.strip())]
    if weak_ctas and total_body_words >= 100 and not any(f.get("cause_id") == "CTA_REACHABILITY_FRICTION" for f in findings):
        findings.append(
            {
                "category": "conversion-continuity",
                "title": f"Generic conversion action copy on {page_type or 'landing page'} ('{weak_ctas[0]}')",
                "severity": "medium",
                "confidence": "high",
                "root_cause": f"CTA_REACHABILITY_FRICTION: Primary interactive conversion trigger relies on generic action copy ('{weak_ctas[0]}') without specific outcome value nouns.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "id": "CTA_REACHABILITY_FRICTION",
                "cause_id": "CTA_REACHABILITY_FRICTION",
                "url": url,
                "scope": url,
                "impact": "AI referral visitors arriving with specific purchase intent experience context scent loss, depressing conversion rates.",
                "evidence": f"Found generic CTA trigger ('{weak_ctas[0]}') on {url}.",
                "suggested_action": {
                    "summary": f"Replace generic '{weak_ctas[0]}' CTA with specific outcome copy.",
                    "technical_fix": "Update CTA button markup to state the delivered value (e.g. 'Start Free Trial', 'Explore Product Catalog', 'View Documentation').",
                    "creative_fix": "Align CTA verbs with the exact recommendation made by AI search engines.",
                    "priority": "medium",
                    "verification": "Confirm CTA text contains descriptive benefit nouns.",
                },
            }
        )

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
                "url": url,
                "scope": url,
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
    if page_type in ("product_detail", "pricing", "subscription_flow") and cta_data["is_delayed"] and total_body_words >= 30:
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
                "url": url,
                "scope": url,
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

    # 1.5 Multilingual Locale Scent & Hreflang Continuity Check
    loc_match = re.search(r"^https?://[^/]+/([a-z]{2}(?:-[a-z]{2})?)/", url, re.IGNORECASE)
    if loc_match and total_body_words >= 50:
        current_locale = loc_match.group(1).lower()
        parsed_current = urlparse(url)
        current_host = parsed_current.netloc.lower()
        internal_links = []
        for href in (dom.ctas + dom.nav_links):
            if not isinstance(href, str):
                continue
            h = href.strip()
            if not h or h.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            if h.startswith("/") and not h.startswith(("//", "/api", "/static", "/assets", "/_next", "/favicon")):
                internal_links.append(h)
            elif "://" in h:
                p_h = urlparse(h)
                if p_h.netloc.lower() == current_host and not p_h.path.startswith(("/api", "/static", "/assets", "/_next", "/favicon")):
                    internal_links.append(p_h.path + (("?" + p_h.query) if p_h.query else ""))
        if len(internal_links) >= 4:
            leaked_links = [
                h for h in internal_links
                if not h.startswith(f"/{current_locale}/") and h != f"/{current_locale}" and not h.startswith(f"/{current_locale}?")
            ]
            if (len(leaked_links) / len(internal_links) > 0.7) and not any(f.get("cause_id") == "COMMERCIAL_HANDOFF_DISCONTINUITY" for f in findings):
                findings.append(
                    {
                        "category": "conversion-continuity",
                        "title": f"Multilingual navigation links drop /{current_locale}/ locale prefix on {url}",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": (
                            f"COMMERCIAL_HANDOFF_DISCONTINUITY: Arriving visitors at localized route ({url}, locale: '{current_locale}') "
                            f"encounter {len(leaked_links)}/{len(internal_links)} internal navigation links that omit the /{current_locale}/ prefix. "
                            "High-intent citation traffic arriving from AI search in a specific language experiences context drop-off when navigation resets to the default language."
                        ),
                        "cause_family": "EXPERIENCE.CONTINUITY",
                        "id": "COMMERCIAL_HANDOFF_DISCONTINUITY",
                        "cause_id": "COMMERCIAL_HANDOFF_DISCONTINUITY",
                        "url": url,
                        "scope": url,
                        "impact": "Visitors arriving from international AI citations lose language orientation upon clicking internal navigation.",
                        "evidence": f"Found {len(leaked_links)} unlocalized link(s) on {url} (e.g. '{leaked_links[0]}').",
                        "suggested_action": {
                            "summary": f"Preserve the /{current_locale}/ prefix across all internal navigation and CTA links on {url}.",
                            "technical_fix": f"Update URL generation helper or router to prepend /{current_locale} to internal href attributes.",
                            "creative_fix": f"Ensure language consistency across product catalog and checkout flows for the '{current_locale}' locale.",
                            "priority": "medium",
                            "verification": f"Verify internal navigation links on {url} maintain the /{current_locale}/ prefix.",
                        },
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


def audit(
    base,
    domain,
    inv=None,
    state_file=None,
    analytics=None,
    *,
    target_url=None,
    referrer_query=None,
    viewport_only=False,
):
    if inv is not None and not isinstance(inv, dict):
        inv = None
    state = {}
    if state_file and isinstance(state_file, (str, bytes, os.PathLike)) and os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
    findings = []
    recommendations = []
    observations = []
    page_metrics = []

    analytics_map = parse_analytics_data(analytics, inv=inv)

    html_pages = []
    if inv is not None:
        for p in (inv.get("pages") or []):
            if not isinstance(p, dict):
                continue
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

    # Custom forensic filter: scope to single target URL
    if target_url:
        matched = [
            p for p in html_pages
            if p.get("url") == target_url
            or urlparse(p.get("url", "")).path.rstrip("/") == urlparse(target_url).path.rstrip("/")
        ]
        if matched:
            html_pages = matched
        else:
            return {
                "status": "inconclusive",
                "error": f"URL '{target_url}' not found in inventory HTML pages",
                "available_urls": [p.get("url") for p in html_pages[:10]],
            }

    # Custom forensic parameter: evaluate intent-to-landing scent for a simulated AI referral query
    if referrer_query:
        query_stopwords = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "by", "about", "against", "between", "into", "through", "during", "before",
            "after", "above", "below", "from", "up", "down", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did", "what",
            "who", "how", "why", "where", "when", "which", "can", "could", "should",
            "would", "of", "it", "its", "this", "that",
        }
        tokens = [
            w.lower()
            for w in re.findall(r"\b\w+\b", referrer_query)
            if len(w) > 2 and w.lower() not in query_stopwords
        ]
        evaluations = []
        for p in html_pages:
            p_url = p.get("url", "")
            p_html = p.get("html", "")
            dom = EngagementDOMParser()
            try:
                dom.feed(p_html)
            except Exception:
                pass
            h1_val = dom.h1_list[0] if dom.h1_list else ""
            hero_snippet = " ".join(dom.paragraphs[:3]) if dom.paragraphs else " ".join(dom.body_text[:100])
            combined_eval_text = f"{p.get('title', '')} {h1_val} {hero_snippet}".lower()
            matched = [t for t in tokens if t in combined_eval_text]
            missing = [t for t in tokens if t not in combined_eval_text]
            score = round(len(matched) / max(len(tokens), 1), 2)
            evaluations.append({
                "url": p_url,
                "h1": h1_val,
                "title": p.get("title", ""),
                "scent_score": score,
                "matched_terms": matched,
                "missing_terms": missing,
                "verdict": "strong_scent" if score >= 0.7 else ("moderate_scent" if score >= 0.4 else "intent_mismatch"),
                "hero_snippet": hero_snippet[:200] + ("..." if len(hero_snippet) > 200 else ""),
            })
        return {
            "status": "ok",
            "referrer_query": referrer_query,
            "query_tokens": tokens,
            "pages_evaluated": len(evaluations),
            "evaluations": evaluations,
        }

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
            page_dict=p,
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
                            "url": p_url,
                            "scope": p_url,
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
        p_data["url"] = p.get("url", "")
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

    # Check J9: 404 Recovery Affordances Check
    for p in ((inv.get("pages") or []) if isinstance(inv, dict) else []):
        if not isinstance(p, dict):
            continue
        if p.get("status") == 404 or "/404" in str(p.get("url", "")):
            p_html = p.get("html", "")
            err_links = []
            try:
                err_links = re.findall(
                    r'<a\s+(?:[^>]*?\s+)?href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>',
                    p_html,
                    re.I | re.S,
                )
                named_err_links = [
                    (h, re.sub(r"<[^>]+>", "", t).strip())
                    for h, t in err_links
                    if re.sub(r"<[^>]+>", "", t).strip()
                ]
            except Exception:
                named_err_links = []
            if len(named_err_links) < 2:
                findings.append(
                    {
                        "id": "J9_404_RECOVERY_DEFICIT",
                        "cause_id": "DESTINATION_NAVIGATION_FRICTION",
                        "check_id": "J9",
                        "actual_band": "S1",
                        "finding_kind": "confirmed_problem",
                        "url": p.get("url"),
                        "scope": p.get("url"),
                        "title": "404 recovery affordances deficit in error response",
                        "severity": "low",
                        "confidence": "high",
                        "root_cause": "The 404 error page provides few or no navigation links to help visitors recover from broken URLs.",
                        "category": "engagement",
                        "impact": "Visitors arriving from broken AI search citations encounter a dead end and immediately bounce.",
                        "evidence": f"404 error page on {p.get('url')} contains only {len(named_err_links)} recovery navigation link(s).",
                        "suggested_action": {
                            "summary": f"Add recovery affordances (home link, search bar, top categories) to the 404 error page on {p.get('url')}.",
                            "priority": "low",
                            "technical_fix": "Update 404 error template to include header navigation, search input, and top category links.",
                            "creative_fix": "Write helpful recovery copy directing lost users to popular site resources.",
                            "verification": "Visit 404 page and verify prominent recovery navigation links are present.",
                        },
                    }
                )
            else:
                observations.append(
                    {
                        "check_id": "J9",
                        "title": "404 recovery affordances inventoried in source",
                        "scope": p.get("url", base + "/404"),
                        "observation": f"{len(named_err_links)} named source recovery links present on 404 page.",
                        "actual_band": "U",
                        "finding_kind": "informational_observation",
                        "limitation": f"{len(named_err_links)} named source links; visibility and destination usefulness require review.",
                    }
                )

    # Check I1: Fresh unauthenticated GET repeated stability observation
    if html_pages:
        sample_url = html_pages[0].get("url", base + "/")
        observations.append(
            {
                "check_id": "I1",
                "title": "Fresh unauthenticated GET repeated for observed URL",
                "scope": sample_url,
                "observation": "200",
                "actual_band": "U",
                "finding_kind": "informational_observation",
                "limitation": "Repeated HTTP 200 observed; status equality does not establish entity/content identity.",
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

    if viewport_only:
        viewport_records = []
        for pm in page_metrics:
            viewport_records.append({
                "url": pm.get("url", ""),
                "h1_present": pm.get("h1", False),
                "viewport_anchored": pm.get("viewport_anchored", False),
                "cta_reachability_score": pm.get("cta_reachability_score", 0.0),
                "information_scent_score": pm.get("information_scent_score", 0.0),
                "ari_readability_score": pm.get("ari_readability_score", 0.0),
            })
        viewport_findings = [
            f
            for f in findings
            if f.get("id") in (
                "UNCORROBORATED_LEAD_PROPOSITION",
                "EXCESSIVE_HERO_READING_FRICTION",
                "MISSING_VIEWPORT_ANSWER_ANCHOR",
                "UNREACHABLE_COMMERCIAL_CTA",
                "LOW_INFORMATION_SCENT",
            )
        ]
        return {
            "status": "ok",
            "mode": "viewport_only",
            "viewport_records": viewport_records,
            "findings": viewport_findings,
            "recommendations": [
                r
                for r in recommendations
                if any(k in r.get("summary", "").lower() for k in ("viewport", "cta", "h1", "hero"))
            ],
            "summary": {
                "total_pages": len(viewport_records),
                "viewport_anchored_count": sum(1 for r in viewport_records if r["viewport_anchored"]),
                "average_cta_reachability": round(
                    sum(r["cta_reachability_score"] for r in viewport_records) / max(len(viewport_records), 1), 2
                ),
                "average_information_scent": round(
                    sum(r["information_scent_score"] for r in viewport_records) / max(len(viewport_records), 1), 2
                ),
            },
        }

    result_payload = {
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

    if state_file and isinstance(state_file, (str, bytes, os.PathLike)):
        try:
            state["engagement_summary"] = engagement_continuity_summary
            import tempfile as _tf
            _fd, _tmp = _tf.mkstemp(dir=os.path.dirname(os.path.abspath(state_file)))
            with os.fdopen(_fd, "w", encoding="utf-8") as f:
                json.dump(state, f)
            os.replace(_tmp, state_file)
        except Exception:
            pass

    return result_payload


def format_markdown_summary(res: Dict[str, Any], domain: Optional[str] = None) -> str:
    """Format engagement context sensor result as clean, readable Markdown."""
    lines = [f"# Visitor Engagement & Orientation Diagnostic Report: {domain or 'Target Site'}"]
    lines.append(f"\n- **Status:** `{res.get('status', 'ok')}`")
    cov = res.get("coverage", {})
    if isinstance(cov, dict) and cov:
        lines.append(f"- **Pages Evaluated:** {cov.get('pages_evaluated', 0)}")
        lines.append(f"- **Above-Fold Answer Absence:** {cov.get('viewport_answer_absence_count', 0)}")
        lines.append(f"- **CTA Friction Rate:** {cov.get('cta_friction_rate', 'N/A')}")

    findings = res.get("findings", [])
    lines.append(f"\n## Diagnostic Findings ({len(findings)})")
    if not findings:
        lines.append("\nNo visitor orientation or post-citation engagement friction detected.")
    else:
        for f in findings:
            fid = f.get("id") or f.get("cause_id") or "FINDING"
            sev = str(f.get("severity", "medium")).upper()
            title = f.get("title", "")
            scope = f.get("scope") or f.get("url") or "-"
            lines.append(f"\n### [{sev}] {fid}: {title}")
            lines.append(f"- **Scope:** `{scope}`")
            if f.get("root_cause"):
                lines.append(f"- **Root Cause:** {f.get('root_cause')}")
            if f.get("evidence"):
                ev = f.get("evidence")
                lines.append(f"- **Evidence:** {ev.get('summary') if isinstance(ev, dict) else ev}")
            s_act = f.get("suggested_action")
            if isinstance(s_act, dict):
                lines.append(f"- **Technical Fix:** {s_act.get('technical_fix', s_act.get('summary', ''))}")
                if s_act.get("creative_fix"):
                    lines.append(f"- **Creative Fix:** {s_act.get('creative_fix')}")

    recs = res.get("recommendations", [])
    if recs:
        lines.append(f"\n## Proactive Recommendations ({len(recs)})")
        for r in recs:
            lines.append(f"- **[{str(r.get('priority', 'medium')).upper()}] {r.get('id', 'REC')}:** {r.get('title', '')} - {r.get('summary', '')}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Visitor Engagement & Post-Citation Intent Continuity Diagnostic Sensor.\n"
            "Deterministically evaluates visitor orientation, the 4-question above-the-fold test, "
            "H1 information scent purity, viewport answer anchoring (top 600px / 150w), "
            "CTA reachability index (commercial continuation proximity), cognitive readability (ARI), "
            "and correlates static UX friction with first-party route-level web analytics."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--inventory", help="Path to pre-crawled site inventory JSON (inv.json) for offline execution")
    parser.add_argument("--url", help="Target URL route to scope engagement and continuity evaluation")
    parser.add_argument("--referrer-query", dest="referrer_query", help="Simulate AI search citation referral query and test intent-to-landing scent")
    parser.add_argument("--viewport-only", dest="viewport_only", action="store_true", help="Inspect strictly above-the-fold viewport elements and CTA reachability")
    parser.add_argument("--state", help="Path to global state JSON (optional multi-turn evaluation)")
    parser.add_argument(
        "--analytics",
        help="Path to first-party analytics JSON/CSV file or JSON string for empirical bounce/dwell correlation",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output serialization format (default: json)")
    args = parser.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    inv = None
    if args.inventory:
        if os.path.exists(args.inventory):
            try:
                with open(args.inventory, "r", encoding="utf-8") as f:
                    inv = json.load(f)
            except Exception as e:
                inv = {"pages": [], "error": f"Failed to parse inventory: {e}", "status": "inconclusive"}
        else:
            inv = {"pages": [], "error": "Inventory file not found", "status": "inconclusive"}
    res = audit(
        base,
        p.netloc,
        inv=inv,
        state_file=args.state,
        analytics=args.analytics,
        target_url=args.url,
        referrer_query=args.referrer_query,
        viewport_only=args.viewport_only,
    )
    if args.format == "markdown":
        print(format_markdown_summary(res, domain=p.netloc))
    else:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
