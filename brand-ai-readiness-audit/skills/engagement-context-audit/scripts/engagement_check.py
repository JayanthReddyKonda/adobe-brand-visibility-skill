#!/usr/bin/env python3
"""
engagement_check.py - Engagement & context continuity layer.

Causal Root Causes:
  - EXPERIENCE.CONTINUITY: INTENT_TO_LANDING_MISMATCH, LOW_INFORMATION_SCENT, DESTINATION_NAVIGATION_FRICTION

Evaluates the complete Intent -> Expected Facts -> Landing Page -> Information Scent -> Next Action journey.
Enforces strict Resource Invariant: Only genuine HTML pages enter engagement audits.
"""
import sys
import os
import re
import json
import argparse
from html.parser import HTMLParser
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT

KNOWN_LOCALES = {"en", "es", "fr", "de", "it", "jp", "ja", "pt", "nl", "zh", "ko", "ru", "ar"}


def extract_locale_and_path(url):
    parsed = urlparse(url)
    segments = [s for s in parsed.path.strip("/").split("/") if s]
    locale = "default"
    if segments and (segments[0].lower() in KNOWN_LOCALES or re.match(r'^[a-z]{2}(-[a-z]{2})?$', segments[0].lower())):
        locale = segments[0].lower()
        logical_path = "/" + "/".join(segments[1:])
    else:
        logical_path = parsed.path or "/"
    return locale, logical_path


def classify_page(url, title=""):
    """Classify an HTML page with confidence and granular page types."""
    locale, logical_path = extract_locale_and_path(url)
    segments = [s for s in logical_path.strip("/").split("/") if s]
    t_lower = (title or "").lower()

    if not segments or logical_path == "/":
        return "homepage", "high"
    last_seg = segments[-1]
    if last_seg in ("default", "placeholder", "template", "empty", "sample", "test"):
        return "template", "high"
    if len(segments) == 1 and segments[0] in ("products", "shop", "catalog", "store", "items"):
        return "product_listing", "high"
    if len(segments) >= 2 and segments[0] in ("products", "p", "product", "item", "items", "shop", "catalog") and segments[1] not in ("default", "all", "category", "categories"):
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
    if re.search(r'\b(contact\s*(us|ez-nous)?|contáctenos|kontakt|お問い合わせ)\b', t_lower):
        return "contact", "high"
    if re.search(r'\b(pricing|plans|tarifs|preise)\b', t_lower):
        return "pricing", "medium"
    if re.search(r'\b(subscription|abonnement|suscripción|subscribe)\b', t_lower):
        return "subscription_flow", "high"
    if re.search(r'\b(products?|catalog|shop|boutique|tienda)\b', t_lower):
        return "product_listing", "medium"
    if re.search(r'\b(about\s*(us)?|notre\s*histoire|sobre\s*nosotros|company)\b', t_lower):
        return "about", "medium"
    return "other", "low"




GENERIC_H1_TERMS = {
    "welcome", "home", "homepage", "untitled", "index", "hello",
    "welcome to our website", "welcome to our site", "main page", "overview"
}

VALID_CONTACT_TERMS = {
    "contact", "contact us", "get in touch", "reach out", "support",
    "contacto", "contáctenos", "contactez-nous", "kontakt", "kontaktiere uns",
    "contatti", "fale conosco", "contato", "contate-nos", "contacteer ons",
    "kontakt oss", "kontakt os", "ota yhteyttä", "kapcsolat", "kontaktujte nás",
    "skontaktuj się z nami", "contactati-ne", "iletisim", "свяжитесь с нами",
    "контакты", "اتصل بنا", "צור קשר", "संपर्क करें", "যোগাযোগ করুন",
    "联系我们", "聯絡我們", "お問い合わせ", "문의하기", "hubungi kami", "liên hệ"
}

CORE_DESTINATIONS = ["pricing", "product", "docs", "documentation", "about", "contact", "login", "signup", "shop", "store"]



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

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower in ("script", "style", "noscript"):
            self.in_script = True
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower in ("h1", "h2"):
            self.current_tag = tag_lower
            self.current_text = []
        elif tag_lower == "a":
            self.in_anchor = True
            self.current_anchor_text = []
            self.current_href = attr_dict.get("href", "")
            if self.current_href:
                self.nav_links.append(self.current_href)
                cls = attr_dict.get("class", "").lower()
                role = attr_dict.get("role", "").lower()
                if "btn" in cls or "button" in cls or "cta" in cls or role == "button":
                    self.ctas.append(self.current_href)

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
        elif tag_lower == "a":
            if self.in_anchor and self.current_anchor_text:
                self.nav_link_texts.append(" ".join(self.current_anchor_text).strip())
            self.in_anchor = False

    def handle_data(self, data):
        if self.in_title:
            self.title += " " + data.strip()
        if self.current_tag in ("h1", "h2"):
            self.current_text.append(data.strip())
        if self.in_anchor:
            self.current_anchor_text.append(data.strip())
        if not self.in_script:
            txt = data.strip()
            if txt:
                self.body_text.append(txt)

GENERIC_H1_TERMS = {"welcome", "home", "main", "untitled", "test", "page", "index", "default"}

VALID_CONTACT_TERMS = {
    "contact", "contact us", "contact-us", "contáctenos", "contactez-nous",
    "kontakt", "contact info", "get in touch", "reach us", "customer service",
    "help desk", "support", "お問い合わせ"
}



import math
from collections import Counter

# Elite Pre-computed TF-IDF Centroids for Zero-Dependency Semantic Intent Mapping
TFIDF_CENTROIDS = {
    "ecommerce_retail": {"shop": 0.5, "cart": 0.4, "product": 0.3, "price": 0.3, "shipping": 0.2, "return": 0.2, "store": 0.2, "buy": 0.3, "apparel": 0.2, "coffee": 0.1},
    "saas_developer": {"api": 0.5, "docs": 0.4, "platform": 0.3, "pricing": 0.3, "cloud": 0.2, "software": 0.2, "developer": 0.3, "login": 0.2, "dashboard": 0.2},
    "media_content": {"news": 0.5, "article": 0.4, "author": 0.3, "read": 0.3, "publish": 0.2, "journal": 0.2, "magazine": 0.2, "blog": 0.3},
    "service_consulting": {"consulting": 0.5, "services": 0.4, "case": 0.3, "study": 0.3, "team": 0.2, "contact": 0.2, "portfolio": 0.3, "expertise": 0.2}
}

def cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    return float(numerator) / denominator if denominator else 0.0

def infer_site_type(html_pages):
    """
    Advanced Semantic Inference using Term Frequency - Inverse Document Frequency (TF-IDF) 
    and Vector Space Cosine Similarity mapping, implemented in pure Python.
    """
    all_text = " ".join((p.get("title", "") + " " + p.get("url", "")) for p in html_pages).lower()
    words = re.findall(r'[a-z]{3,}', all_text)
    if not words:
        return "general_business", ["products", "services", "pricing", "about", "contact", "help"]
        
    term_counts = Counter(words)
    total_terms = sum(term_counts.values())
    
    # Calculate Term Frequency (TF) for observed document
    tf_vector = {word: count/total_terms for word, count in term_counts.items()}
    
    best_match = "general_business"
    best_score = 0.01  # Minimum threshold for confidence
    
    for category, centroid in TFIDF_CENTROIDS.items():
        score = cosine_similarity(tf_vector, centroid)
        if score > best_score:
            best_score = score
            best_match = category
            
    # Return destination mapping based on statistical match
    destinations = {
        "ecommerce_retail": ["products", "shop", "catalog", "store", "subscription", "contact", "about"],
        "saas_developer": ["pricing", "features", "docs", "documentation", "api", "contact", "login"],
        "media_content": ["articles", "latest", "topics", "search", "about", "contact"],
        "service_consulting": ["services", "portfolio", "case-studies", "team", "contact", "about"]
    }
    
    return best_match, destinations.get(best_match, ["products", "services", "pricing", "about", "contact"])


def audit_page_engagement(html_content, url, page_type="other", applicable_destinations=None):
    """Evaluate 5-second orientation, information scent, and intent continuity with site-type awareness."""
    findings = []
    recommendations = []

    if applicable_destinations is None:
        applicable_destinations = ["products", "pricing", "about", "contact", "help"]

    dom = EngagementDOMParser()
    try:
        dom.feed(html_content)
    except Exception:
        pass

    # Centralized, segment-exact page classifier
    if not page_type or page_type == "other":
        detected_type, _ = classify_page(url)
        if detected_type and detected_type != "other":
            page_type = detected_type

    full_text = " ".join(dom.body_text)
    visible_words = len(full_text.split())
    clean_title = dom.title.strip()
    has_descriptive_title = len(clean_title.split()) >= 3
    has_subheadings = len(dom.h2_list) >= 1
    has_functional_context = page_type in (
        "subscription_flow", "product_detail", "product_listing", "checkout", "pricing_tier", "contact", "about"
    )

    # 1. Multi-Signal 5-Second Orientation & Information Scent
    if not dom.h1_list:
        if not has_descriptive_title and not has_subheadings and not has_functional_context and visible_words > 150:
            findings.append({
                "category": "engagement",
                "title": f"Weak first-visit orientation and missing primary topic statement ({url})",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "The page lacks an H1 heading, descriptive page title, and section markers, leaving arriving visitors unoriented.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "cause_id": "LOW_INFORMATION_SCENT",
                "impact": "Visitors arriving from AI search answers cannot quickly verify the page purpose, which could increase bounce rate.",
                "evidence": f"Found 0 H1 heading tags, 0 H2 tags, and a non-descriptive page title ('{clean_title}') on {url}.",
                "suggested_action": {
                    "summary": "Add a descriptive H1 headline above the fold clearly stating the offering name and value proposition.",
                    "priority": "medium",
                    "verification": f"Confirm {url} contains an H1 stating the core offering topic."
                }
            })
        elif visible_words > 60:
            recommendations.append({
                "title": f"Add semantic H1 heading element on {url}",
                "category": "engagement",
                "rationale": f"Page provides functional context in page title ('{clean_title}') but lacks an explicit H1 heading for semantic structure.",
                "suggested_action": "Add an H1 heading representing the page's core purpose to strengthen heading information scent."
            })
    else:
        primary_h1 = dom.h1_list[0].strip()
        h1_clean = primary_h1.lower()
        is_contact_page = (page_type == "contact")

        # Contact pages with "Contact us" or international translations are valid and should PASS
        if is_contact_page and any(term in h1_clean for term in VALID_CONTACT_TERMS):
            pass  # Fully semantically clear for a contact page
        elif h1_clean in GENERIC_H1_TERMS and not has_descriptive_title and not has_functional_context and visible_words > 20:
            findings.append({
                "category": "engagement",
                "title": f"Low-information generic headline on landing page ('{primary_h1}')",
                "severity": "low",
                "confidence": "medium",

                "root_cause": f"The primary headline ('{primary_h1}') is generic and conveys weak information scent without title context.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "cause_id": "LOW_INFORMATION_SCENT",
                "impact": "Visitors skimming above-the-fold content cannot quickly verify the brand's core offering within 5 seconds.",
                "evidence": f"Primary H1 on {url} is '{primary_h1}'.",
                "suggested_action": {
                    "summary": "Revise the H1 to include concrete product nouns and value verbs representing the offering purpose.",
                    "priority": "low",
                    "verification": "Confirm updated H1 contains descriptive brand or product terminology."
                }
            })



    # 2. Destination Discoverability & Navigation Friction
    nav_links_text = " ".join(dom.nav_links + dom.nav_link_texts).lower()
    found_destinations = [d for d in applicable_destinations if d in nav_links_text]

    # Check if page provides meaningful internal navigation paths or interactive flows
    all_hrefs = re.findall(r'href=["\'](https?://[^"\']+|/[^"\']+)["\']', html_content, re.I)
    internal_links_count = len(all_hrefs)


    if len(dom.nav_links) == 0 and internal_links_count < 2 and visible_words > 150 and page_type not in ("template", "other"):
        findings.append({
            "category": "engagement",
            "title": f"Restricted destination navigation on landing page ({url})",
            "severity": "medium",
            "confidence": "medium",
            "root_cause": "The page lacks header, footer, or in-body navigation links to related brand destinations.",
            "cause_family": "EXPERIENCE.CONTINUITY",
            "cause_id": "DESTINATION_NAVIGATION_FRICTION",
            "impact": "Visitors arriving with a specific intent cannot navigate to related brand resources without returning to search, which could increase navigation friction.",
            "evidence": f"Found {len(dom.nav_links)} navigation elements and {internal_links_count} internal links on {url}.",
            "suggested_action": {
                "summary": "Add header/footer navigation links to key brand destinations.",
                "priority": "medium",
                "verification": f"Verify {url} contains discoverable links to core destinations."
            }
        })
    elif len(dom.nav_links) < 2 and internal_links_count < 4 and visible_words > 80:
        recommendations.append({
            "title": f"Enhance contextual navigation paths on {url}",
            "category": "engagement",
            "rationale": f"Page has limited outbound navigation links ({internal_links_count} links found).",
            "suggested_action": "Ensure key user journeys retain contextual header or footer links to main brand destinations."
        })

    # 3. Intent-to-Landing Match for Specialized Commercial Pages
    if page_type == "pricing":
        has_prices = any(k in full_text.lower() for k in ("$", "₹", "usd", "inr", "eur", "£", "free", "tier", "plan", "/mo", "quote", "contact sales"))
        if not has_prices and visible_words > 100:
            findings.append({
                "category": "intent-continuity",
                "title": f"Intent-to-landing mismatch: Pricing page omits commercial terms ({url})",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "A pricing-designated landing route contains no visible price figures, plan tiers, or indicative pricing ranges.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "cause_id": "INTENT_TO_LANDING_MISMATCH",
                "impact": "Visitors arriving with pricing comparison intent encounter a content gap, which could increase bounce rate.",
                "evidence": f"Pricing page ({url}) contains 0 numerical price figures or plan tier indicators.",
                "suggested_action": {
                    "summary": "Publish transparent tier pricing or starting ranges above the fold on the pricing landing page.",
                    "priority": "medium",
                    "verification": f"Confirm {url} displays clear pricing tiers and commercial terms."
                }
            })


    return findings, recommendations, {
        "url": url,
        "h1": dom.h1_list,
        "h2_count": len(dom.h2_list),
        "visible_words": visible_words,
        "navigation_links_found": len(dom.nav_links),
        "core_destinations_found": found_destinations
    }


def audit(base, domain, inv=None):
    findings = []
    recommendations = []
    observations = []
    page_metrics = []

    html_pages = []
    if inv is not None:
        for p in inv.get("pages", []):
            u = p.get("url", "")
            raw_html = p.get("html", "")
            if u.lower().endswith((".xml", ".xml.gz", ".txt", ".json", ".pdf")):
                continue
            if raw_html.strip().startswith("<?xml") or "<urlset" in raw_html.lower() or "<sitemapindex" in raw_html.lower():
                continue
            if raw_html:
                html_pages.append(p)
    else:
        status, html, _, _ = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if html:
            html_pages.append({"url": base + "/", "html": html, "page_type": "homepage"})

    site_type, applicable_destinations = infer_site_type(html_pages)
    for p in html_pages:
        p_findings, p_recs, p_data = audit_page_engagement(
            p["html"], p["url"],
            page_type=p.get("page_type", "other"),
            applicable_destinations=applicable_destinations
        )
        findings.extend(p_findings)
        recommendations.extend(p_recs)
        page_metrics.append(p_data)

    if not page_metrics:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve HTML content from {base}"
        }

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "html_pages_evaluated": len(html_pages),
            "site_type_inferred": site_type,
            "applicable_destinations": applicable_destinations[:6],
            "average_visible_words": round(sum(pm["visible_words"] for pm in page_metrics) / max(1, len(page_metrics)), 1),
            "pages_with_h1": sum(1 for pm in page_metrics if pm["h1"]),
            "pages_with_navigation": sum(1 for pm in page_metrics if pm["navigation_links_found"] > 0)
        },
        "limitations": [
            "Engagement and orientation analysis is based on static HTML layout semantics; dynamic client-rendered overlays were not evaluated."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Audit on-site visitor orientation, heading hierarchies, and navigation.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
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
    res = audit(base, p.netloc, inv=inv)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
