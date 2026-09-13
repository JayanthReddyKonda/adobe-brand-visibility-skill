#!/usr/bin/env python3
"""
entity_content_check.py - Entity identity & content answerability audit layer.

Causal Root Causes:
  - ENTITY.IDENTITY: MATERIAL_ENTITY_AMBIGUITY, WEAK_IDENTITY_SIGNALS
  - ENTITY.ANSWERABILITY: INCOMPLETE_OFFER_ATTRIBUTES, MISSING_MATERIAL_FACT, WEAK_ANSWER_SURFACE

Calculates the mathematically reproducible weighted Weighted material-attribute coverage:
  Index = sum(weight_i * present_i) / sum(weight_i)

Enforces strict Resource Invariant:
  - Only genuine HTML pages enter answerability audits (XML sitemaps and feeds are strictly excluded).
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from typing import Any, Dict, Optional
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore

# Weighted Answerability Schema by Page Type (Structured & Measurable Material Attributes)
MATERIAL_ATTRIBUTE_WEIGHTS = {
    "product_detail": {
        "product_name": (0.30, ["product", "item", "model", "sku", "title"]),
        "price": (0.25, ["₹", "$", "usd", "inr", "eur", "£", "price", "starts at", "/mo"]),
        "availability": (0.25, ["schema.org/instock", "schema.org/outofstock", "schema.org/preorder", "availability"]),
        "specifications": (
            0.20,
            ["specifications", "features", "origin", "weight", "capacity", "sla", "dimensions", "details"],
        ),
    },
    "product": {  # Alias for single product pages
        "product_identity": (0.30, ["brand", "manufacturer", "sku", "mpn", "gtin", "model"]),
        "price": (0.25, ["₹", "$", "usd", "inr", "eur", "£", "price", "starts at", "/mo"]),
        "availability": (0.25, ["schema.org/instock", "schema.org/outofstock", "schema.org/preorder", "availability"]),
        "specifications": (
            0.20,
            ["specifications", "features", "origin", "weight", "capacity", "sla", "dimensions", "details"],
        ),
    },
    "product_listing": {
        "catalog_items": (0.40, ["products", "items", "browse", "catalog", "shop", "collection", "filter"]),
        "category_title": (0.30, ["category", "all products", "our products", "shop all", "catalog", "explore"]),
        "action_path": (0.30, ["view", "buy", "details", "add to cart", "shop now", "order"]),
    },
    "category": {
        "catalog_items": (0.40, ["products", "items", "browse", "catalog", "shop", "collection", "filter"]),
        "category_title": (0.30, ["category", "all products", "our products", "shop all", "catalog", "explore"]),
        "action_path": (0.30, ["view", "buy", "details", "add to cart", "shop now", "order"]),
    },
    "subscription_flow": {
        "plan_description": (
            0.35,
            ["subscription", "club", "membership", "recurring", "monthly", "deliveries", "frequency"],
        ),
        "selection_options": (0.35, ["choose", "select", "options", "beans", "grind", "frequency", "tier", "plan"]),
        "cta_action": (0.30, ["subscribe", "join", "sign up", "start", "checkout", "get started"]),
    },
    "pricing": {
        "tier_names": (0.35, ["starter", "pro", "enterprise", "basic", "premium", "tier", "plan", "membership"]),
        "price_figures": (
            0.35,
            ["₹", "$", "usd", "inr", "eur", "£", "/mo", "/month", "/year", "free", "contact sales"],
        ),
        "feature_comparison": (
            0.30,
            ["features", "includes", "comparison", "unlimited", "storage", "users", "benefits"],
        ),
    },
    "service": {
        "service_name": (0.40, ["service", "consulting", "managed", "solution", "offerings"]),
        "deliverables": (0.30, ["deliverables", "capabilities", "scope", "includes", "what we do"]),
        "engagement_model": (0.30, ["hourly", "retainer", "fixed", "timeline", "process", "contact"]),
    },
    "contact": {
        "email_channel": (0.40, ["@", "mailto:", "support@", "sales@", "contact@", "email"]),
        "phone_channel": (0.30, ["tel:", "+", "call", "phone", "hotline"]),
        "location_or_form": (
            0.30,
            ["street", "address", "suite", "floor", "city", "headquarters", "form", "send message", "message"],
        ),
    },
}


class EntityDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_json_ld = False
        self.json_ld_contents = []
        self.og_tags = {}
        self.meta_tags = {}
        self.title = ""
        self.in_title = False
        self.text_content = []
        self.headings = []
        self.current_h = None
        self.current_h_text = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower in ("script", "style"):
            self.in_script = True
            if tag_lower == "script" and "application/ld+json" in attr_dict.get("type", "").lower():
                self.in_json_ld = True
        elif tag_lower == "meta":
            prop = attr_dict.get("property", attr_dict.get("name", "")).lower()
            content = attr_dict.get("content", "")
            if prop and content:
                if prop.startswith("og:"):
                    self.og_tags[prop] = content
                self.meta_tags[prop] = content
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower in ("h1", "h2", "h3"):
            self.current_h = tag_lower
            self.current_h_text = []

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style"):
            self.in_script = False
            self.in_json_ld = False
        elif tag_lower == "title":
            self.in_title = False
        elif tag_lower in ("h1", "h2", "h3"):
            if self.current_h and self.current_h_text:
                self.headings.append((self.current_h, " ".join(self.current_h_text).strip()))
            self.current_h = None

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data)
        elif self.in_title:
            self.title += " " + data.strip()
        elif self.current_h is not None:
            self.current_h_text.append(data)
        elif not self.in_script and data.strip():
            self.text_content.append(data.strip())


def matches_schema_type(entity, target_types):
    """Check if a JSON-LD entity matches target schema types (handling string or list @type)."""
    if not isinstance(entity, dict):
        return False
    raw_t = entity.get("@type", "")
    if isinstance(raw_t, list):
        types = {str(t).lower() for t in raw_t}
    else:
        types = {str(raw_t).lower()}
    return bool(types.intersection({t.lower() for t in target_types}))


def extract_microdata_and_rdfa(html_str: str) -> list:
    """Extract inline HTML Microdata (itemscope/itemtype/itemprop) and RDFa (typeof/property)."""
    entities: list[dict] = []
    if not html_str:
        return entities

    # 1. Microdata scopes
    scope_pattern = re.compile(
        r"<([a-zA-Z0-9]+)[^>]*?\bitemscope\b[^>]*?\bitemtype=['\"]https?://schema\.org/([a-zA-Z0-9_]+)['\"][^>]*>(.*?)</\1>",
        re.DOTALL | re.IGNORECASE,
    )
    for match in scope_pattern.finditer(html_str):
        etype = match.group(2)
        inner = match.group(3)
        props = {}
        prop_pattern = re.compile(
            r"<[^>]*?\bitemprop=['\"]([a-zA-Z0-9_]+)['\"][^>]*?(?:content=['\"]([^'\"]+)['\"]|value=['\"]([^'\"]+)['\"]|>([^<]+)<)",
            re.IGNORECASE,
        )
        for pm in prop_pattern.finditer(inner):
            pname = pm.group(1)
            val = pm.group(2) or pm.group(3) or (pm.group(4).strip() if pm.group(4) else "")
            if val:
                props[pname] = val
        ent = {"@context": "https://schema.org", "@type": etype}
        ent.update(props)
        entities.append(ent)

    # 2. RDFa typeof scopes
    rdfa_pattern = re.compile(
        r"<([a-zA-Z0-9]+)[^>]*?\btypeof=['\"](?:schema:)?([a-zA-Z0-9_]+)['\"][^>]*>(.*?)</\1>",
        re.DOTALL | re.IGNORECASE,
    )
    for match in rdfa_pattern.finditer(html_str):
        etype = match.group(2)
        inner = match.group(3)
        props = {}
        prop_pattern = re.compile(
            r"<[^>]*?\bproperty=['\"](?:schema:)?([a-zA-Z0-9_]+)['\"][^>]*?(?:content=['\"]([^'\"]+)['\"]|>([^<]+)<)",
            re.IGNORECASE,
        )
        for pm in prop_pattern.finditer(inner):
            pname = pm.group(1)
            val = pm.group(2) or (pm.group(3).strip() if pm.group(3) else "")
            if val:
                props[pname] = val
        ent = {"@context": "https://schema.org", "@type": etype}
        ent.update(props)
        entities.append(ent)

    return entities


def parse_json_ld(raw_json_list, raw_html=""):
    """Extract Schema.org typed objects from JSON-LD, Microdata, and RDFa with decoupled @graph resolution."""
    raw_objects = []
    for raw in raw_json_list:
        try:
            data = json.loads(raw)
            to_process = data if isinstance(data, list) else [data]
            for item in to_process:
                if isinstance(item, dict) and "@graph" in item and isinstance(item["@graph"], list):
                    raw_objects.extend(item["@graph"])
                elif isinstance(item, dict):
                    raw_objects.append(item)
        except Exception:
            pass

    if raw_html:
        raw_objects.extend(extract_microdata_and_rdfa(raw_html))

    # 1. Index all entities by @id
    id_map = {}
    for obj in raw_objects:
        if isinstance(obj, dict) and "@id" in obj and isinstance(obj["@id"], str):
            id_map[obj["@id"].strip()] = obj

    # 2. Resolve references (link Offer nodes, Brand nodes, etc.)
    resolved_entities = []
    for obj in raw_objects:
        if not isinstance(obj, dict):
            continue
        entity = dict(obj)
        if "offers" in entity:
            offers = entity["offers"]
            if isinstance(offers, dict) and "@id" in offers and offers["@id"] in id_map:
                entity["offers"] = id_map[offers["@id"]]
            elif isinstance(offers, list):
                entity["offers"] = [
                    id_map.get(o["@id"], o) if isinstance(o, dict) and "@id" in o and o["@id"] in id_map else o
                    for o in offers
                ]

        for rel in ("brand", "manufacturer", "publisher", "provider", "author", "organizer"):
            if rel in entity and isinstance(entity[rel], dict) and "@id" in entity[rel]:
                target_id = entity[rel]["@id"]
                if target_id in id_map:
                    entity[rel] = id_map[target_id]

        resolved_entities.append(entity)

    # 3. Invert itemOffered references (link decoupled Offer back into target Product)
    for obj in raw_objects:
        if isinstance(obj, dict) and matches_schema_type(obj, ("offer", "aggregateoffer")):
            item_offered = obj.get("itemOffered")
            if isinstance(item_offered, dict) and "@id" in item_offered and item_offered["@id"] in id_map:
                prod = id_map[item_offered["@id"]]
                if "offers" not in prod:
                    prod["offers"] = []
                elif isinstance(prod["offers"], dict):
                    prod["offers"] = [prod["offers"]]
                if isinstance(prod["offers"], list) and obj not in prod["offers"]:
                    prod["offers"].append(obj)

    return resolved_entities


def _kw_in_text(kw: str, text: str) -> bool:
    """Helper to check if a keyword is present in text, using word boundaries for alphanumeric terms."""
    kw_clean = kw.lower().strip()
    if not kw_clean or not text:
        return False
    if re.match(r"^[a-zA-Z0-9_\-]+$", kw_clean):
        return bool(re.search(r"\b" + re.escape(kw_clean) + r"\b", text))
    return kw_clean in text


def evaluate_page_answerability(page_type, html_content, dom, url, structured_entities, page_dict=None):
    if page_type not in MATERIAL_ATTRIBUTE_WEIGHTS:
        return None

    # Text corpus preparation from DOM
    dom_text_list = dom.text_content if dom and hasattr(dom, "text_content") else []
    dom_text = " ".join(dom_text_list).lower()
    headings_text = " ".join(h[1] for h in dom.headings).lower() if dom and hasattr(dom, "headings") else ""
    title_text = (dom.title if dom and hasattr(dom, "title") else "").lower()
    visible_text = f"{title_text} {headings_text} {dom_text}".strip()
    html_lower = (html_content or "").lower()

    # 1. Product Detail and Single Product Pages
    if page_type in ("product_detail", "product"):
        products = [e for e in (structured_entities or []) if matches_schema_type(e, ["Product"])]
        if not products:
            return {"status": "missing_entity"}

        weights_cfg = MATERIAL_ATTRIBUTE_WEIGHTS.get(page_type, MATERIAL_ATTRIBUTE_WEIGHTS["product_detail"])
        results = []
        for p in products:
            offers = p.get("offers", {})
            offers_list = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []

            facts = {}
            for attr_name, (_weight, kws) in weights_cfg.items():
                kw_match = any(_kw_in_text(kw, visible_text) for kw in kws)
                if attr_name in ("product_name", "product_identity"):
                    has_entity_name = bool(
                        (p.get("name") and str(p.get("name")).strip())
                        or (p.get("title") and str(p.get("title")).strip())
                        or p.get("sku")
                        or p.get("mpn")
                        or p.get("gtin")
                        or p.get("model")
                        or (attr_name == "product_identity" and p.get("brand"))
                    )
                    has_dom_name = bool(
                        (headings_text.strip() or title_text.strip())
                        and any(_kw_in_text(kw, visible_text) for kw in kws if kw != "product")
                    )
                    facts[attr_name] = bool(has_entity_name or has_dom_name)
                elif attr_name == "price":
                    has_price = any(
                        isinstance(o, dict)
                        and (
                            (o.get("price") is not None and str(o.get("price")).strip() != "")
                            or (o.get("lowPrice") is not None and str(o.get("lowPrice")).strip() != "")
                        )
                        for o in offers_list
                    )
                    has_dom_price = bool(
                        re.search(
                            r"([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b)\s*\d+(\.\d{2})?|\d+(\.\d{2})?\s*([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b)",
                            visible_text,
                            re.I,
                        )
                    )
                    has_price_kw = any(_kw_in_text(kw, visible_text) for kw in ("price", "starts at", "/mo"))
                    facts[attr_name] = bool(has_price or has_dom_price or has_price_kw)
                elif attr_name == "availability":
                    has_avail = any(
                        isinstance(o, dict)
                        and any(
                            term in str(o.get("availability", "")).lower()
                            for term in ("instock", "in stock", "preorder", "outofstock", "out of stock", "discontinued")
                        )
                        for o in offers_list
                    )
                    has_dom_avail = any(
                        term in visible_text
                        for term in ("instock", "in stock", "preorder", "pre-order", "out of stock", "outofstock")
                    )
                    facts[attr_name] = bool(has_avail or has_dom_avail)
                elif attr_name == "specifications":
                    has_specs = bool(
                        p.get("sku")
                        or p.get("model")
                        or p.get("weight")
                        or p.get("description")
                        or p.get("additionalProperty")
                    )
                    facts[attr_name] = bool(has_specs or kw_match)
                else:
                    facts[attr_name] = bool(kw_match)

            score = sum(weights_cfg[k][0] for k, v in facts.items() if v and k in weights_cfg)
            results.append({"status": "present", "facts": facts, "score": round(score, 2)})

        return {"status": "present", "results": results}

    # 2. Non-Product Pages (pricing, subscription_flow, service, contact, product_listing, category)
    weights_cfg = MATERIAL_ATTRIBUTE_WEIGHTS[page_type]
    facts = {}
    for attr_name, (_weight, kws) in weights_cfg.items():
        kw_match = any(_kw_in_text(kw, visible_text) for kw in kws)
        if page_type == "pricing":
            if attr_name == "tier_names":
                has_entity_name = any(
                    matches_schema_type(e, ["Offer", "Product", "PriceSpecification", "Service"])
                    and bool(e.get("name"))
                    for e in (structured_entities or [])
                )
                facts[attr_name] = bool(has_entity_name or kw_match)
            elif attr_name == "price_figures":
                has_entity_price = any(
                    matches_schema_type(e, ["Offer", "PriceSpecification", "Product"])
                    and (
                        (e.get("price") is not None and str(e.get("price")).strip() != "")
                        or (e.get("lowPrice") is not None and str(e.get("lowPrice")).strip() != "")
                    )
                    for e in (structured_entities or [])
                )
                has_regex_price = bool(
                    re.search(
                        r"([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b)\s*\d+(\.\d{2})?|\d+(\.\d{2})?\s*([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b|\/mo|\/month|\/year)",
                        visible_text,
                        re.I,
                    )
                )
                has_price_kw = any(_kw_in_text(kw, visible_text) for kw in ("free", "contact sales", "/mo", "/month", "/year"))
                facts[attr_name] = bool(has_entity_price or has_regex_price or has_price_kw)
            elif attr_name == "feature_comparison":
                has_entity_features = any(
                    matches_schema_type(e, ["Product", "Offer", "Service"])
                    and (e.get("description") or e.get("additionalProperty") or e.get("hasOfferCatalog"))
                    for e in (structured_entities or [])
                )
                has_html_table = "<table" in html_lower or "<tr" in html_lower
                facts[attr_name] = bool(has_entity_features or has_html_table or kw_match)
            else:
                facts[attr_name] = bool(kw_match)

        elif page_type == "subscription_flow":
            if attr_name == "plan_description":
                has_desc = any(
                    matches_schema_type(e, ["Product", "Offer", "Service"])
                    and bool(e.get("description") or e.get("name"))
                    for e in (structured_entities or [])
                )
                facts[attr_name] = bool(has_desc or kw_match)
            elif attr_name == "selection_options":
                has_options_markup = "<select" in html_lower or 'type="radio"' in html_lower or 'type="checkbox"' in html_lower
                has_entity_options = any(
                    matches_schema_type(e, ["OfferCatalog", "ItemList"])
                    or bool(e.get("additionalProperty"))
                    for e in (structured_entities or [])
                )
                facts[attr_name] = bool(has_options_markup or has_entity_options or kw_match)
            elif attr_name == "cta_action":
                has_btn = "<button" in html_lower or 'type="submit"' in html_lower or 'type="button"' in html_lower
                cta_kws = r"|".join(re.escape(k) for k in weights_cfg["cta_action"][1])
                has_action_elem = bool(
                    re.search(
                        r"<(?:a|button)\s+[^>]*>(?:[^<]*(?:" + cta_kws + r")[^<]*)<\/(?:a|button)>",
                        html_lower,
                        re.I,
                    )
                )
                has_pre_cta = bool(page_dict and any(c.get("is_commercial_cta") for c in page_dict.get("ctas", [])))
                facts[attr_name] = bool(has_btn or has_action_elem or has_pre_cta)
            else:
                facts[attr_name] = bool(kw_match)

        elif page_type == "service":
            if attr_name == "service_name":
                has_svc_name = any(
                    matches_schema_type(e, ["Service", "ProfessionalService", "Product"])
                    and bool(e.get("name") or e.get("serviceType"))
                    for e in (structured_entities or [])
                )
                has_dom_svc = bool(
                    (headings_text.strip() or title_text.strip())
                    and any(_kw_in_text(kw, visible_text) for kw in kws)
                )
                facts[attr_name] = bool(has_svc_name or has_dom_svc or kw_match)
            elif attr_name == "deliverables":
                has_deliverables = any(
                    matches_schema_type(e, ["Service", "ProfessionalService"])
                    and (e.get("description") or e.get("offers") or e.get("hasOfferCatalog"))
                    for e in (structured_entities or [])
                )
                facts[attr_name] = bool(has_deliverables or kw_match)
            elif attr_name == "engagement_model":
                has_model = any(
                    matches_schema_type(e, ["Service", "ProfessionalService"])
                    and (e.get("termsOfService") or e.get("hoursAvailable") or e.get("offers"))
                    for e in (structured_entities or [])
                )
                facts[attr_name] = bool(has_model or kw_match)
            else:
                facts[attr_name] = bool(kw_match)

        elif page_type == "contact":
            if attr_name == "email_channel":
                has_email_entity = any(bool(e.get("email")) for e in (structured_entities or []))
                has_email_text = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", visible_text))
                has_mailto = "mailto:" in html_lower
                has_email_addr = bool(re.search(r"\b(?:support|sales|contact|help|info)@[a-zA-Z0-9.-]+\b", visible_text, re.I))
                has_pre_email = bool(page_dict and page_dict.get("contact_info", {}).get("emails"))
                facts[attr_name] = bool(has_email_entity or has_email_text or has_mailto or has_email_addr or has_pre_email)
            elif attr_name == "phone_channel":
                has_phone_entity = any(bool(e.get("telephone")) for e in (structured_entities or []))
                has_phone_text = bool(
                    re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", visible_text)
                    or re.search(r"\+\d{1,3}[-.\s]?\d{4,}", visible_text)
                )
                has_tel = "tel:" in html_lower
                has_phone_digits = bool(re.search(r"\b(?:call|phone|hotline)\b[^\d\n\r]{0,20}\d{3,}", visible_text, re.I))
                has_pre_phone = bool(page_dict and page_dict.get("contact_info", {}).get("phones"))
                facts[attr_name] = bool(has_phone_entity or has_phone_text or has_tel or has_phone_digits or has_pre_phone)
            elif attr_name == "location_or_form":
                has_loc_entity = any(
                    matches_schema_type(e, ["PostalAddress", "LocalBusiness", "Place", "ContactPoint"])
                    and (e.get("address") or e.get("contactPoint"))
                    for e in (structured_entities or [])
                )
                has_form = "<form" in html_lower
                facts[attr_name] = bool(has_loc_entity or has_form or kw_match)
            else:
                facts[attr_name] = bool(kw_match)

        elif page_type in ("product_listing", "category"):
            if attr_name == "catalog_items":
                has_catalog = any(matches_schema_type(e, ["ItemList", "Product", "OfferCatalog"]) for e in (structured_entities or []))
                facts[attr_name] = bool(has_catalog or kw_match)
            elif attr_name == "category_title":
                has_cat_title = any(matches_schema_type(e, ["CollectionPage", "ItemList"]) and bool(e.get("name")) for e in (structured_entities or []))
                facts[attr_name] = bool(has_cat_title or bool(title_text) or kw_match)
            elif attr_name == "action_path":
                has_links = bool(re.search(r"<(?:a|button)\s+[^>]*>(?:[^<]*(?:view|buy|detail|cart|shop|order)[^<]*)<\/(?:a|button)>", html_lower))
                facts[attr_name] = bool(has_links or kw_match)
            else:
                facts[attr_name] = bool(kw_match)
        else:
            facts[attr_name] = bool(kw_match)

    score = sum(weights_cfg[k][0] for k, v in facts.items() if v and k in weights_cfg)
    results = [{"status": "present", "facts": facts, "score": round(score, 2)}]
    return {"status": "present", "results": results}


def inspect_target_entity(inv, base, domain, target_url):
    """Forensically inspect Schema.org JSON-LD and answerability for a single target URL."""
    norm_url = target_url.strip()
    if not norm_url.startswith("http"):
        norm_url = f"{base.rstrip('/')}/{norm_url.lstrip('/')}"
    p_path = urlparse(norm_url).path or "/"

    page_data = None
    if inv and inv.get("pages"):
        for p in inv["pages"]:
            if p.get("url") == norm_url or urlparse(p.get("url", "")).path == p_path:
                page_data = p
                break

    if not page_data:
        status, html, headers, err = safe_fetch(norm_url, timeout=10, max_bytes=2 * 1024 * 1024)
        page_data = {"url": norm_url, "status": status, "html": html, "headers": headers, "error": err}

    p_html = page_data.get("html") or page_data.get("raw_html") or ""
    dom = EntityDOMParser()
    try:
        dom.feed(p_html)
    except Exception:
        pass

    json_ld_nodes = parse_json_ld(dom.json_ld_contents, p_html)
    types_found = [str(n.get("@type", "")) for n in json_ld_nodes if isinstance(n, dict) and n.get("@type")]

    p_type = page_data.get("page_type") or "content"
    ans_result = evaluate_page_answerability(p_type, p_html, dom, norm_url, json_ld_nodes, page_dict=page_data)

    return {
        "url": norm_url,
        "path": p_path,
        "page_type": p_type,
        "total_json_ld_blocks": len(dom.json_ld_contents),
        "total_entities_extracted": len(json_ld_nodes),
        "schema_types_present": types_found,
        "answerability": ans_result,
        "entities": json_ld_nodes[:20],
    }


def audit(base, domain, inv=None, state_file=None, target_url=None, schema_type=None, answerability_only=False):
    if inv is not None and not isinstance(inv, dict):
        inv = None
    state: Dict[str, Any] = {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}
    if state_file and os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
    findings, recommendations, observations = [], [], []

    # 1. Filter genuine HTML pages from inventory
    html_pages = []
    if inv is not None:
        for p in (inv.get("pages", []) if isinstance(inv, dict) else []):
            if not isinstance(p, dict):
                continue
            u = p.get("url") or ""
            raw_html = p.get("html") or ""
            if not u or not raw_html:
                continue
            # Strict non-HTML / sitemap rejection
            if u.lower().endswith((".xml", ".xml.gz", ".txt", ".json", ".pdf")):
                continue
            if (
                raw_html.strip().startswith("<?xml")
                or "<urlset" in raw_html.lower()
                or "<sitemapindex" in raw_html.lower()
            ):
                continue
            if (
                p.get("resource_type") == "html"
                or "<html" in raw_html.lower()
                or "<!doctype html" in raw_html.lower()
                or p.get("page_type") == "homepage"
            ):
                html_pages.append(p)
    else:
        status, html, _headers, _ = safe_fetch(base + "/", timeout=10, max_bytes=2 * 1024 * 1024)
        if html:
            html_pages.append(
                {"url": base + "/", "status": status, "resource_type": "html", "page_type": "homepage", "html": html}
            )

    if not html_pages:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not reach {base} or no HTML pages found",
        }

    home_page = next((p for p in html_pages if p.get("page_type") == "homepage"), html_pages[0])
    home_html = home_page.get("html", "")

    dom = EntityDOMParser()
    try:
        dom.feed(home_html)
    except Exception:
        pass

    json_ld_entities = parse_json_ld(dom.json_ld_contents, home_html)

    # 2. Organization Entity Recognition (supports array @type)
    org_entity = None
    for e in json_ld_entities:
        if matches_schema_type(e, ("organization", "corporation", "brand", "localbusiness")):
            org_entity = e
            break

    og_site_name = dom.og_tags.get("og:site_name")
    brand_name = (
        (org_entity.get("name") if org_entity and isinstance(org_entity.get("name"), str) else None)
        or og_site_name
        or dom.title.replace(" - ", "|").replace(" | ", "|").split("|")[0].split("|")[0].strip()
    )

    if not org_entity:
        og_note = f" (og:site_name '{og_site_name}' detected, but machine search engines require explicit Schema.org Organization JSON-LD)" if og_site_name else " (no og:site_name detected)"
        findings.append(
            {
                "category": "entity-identity",
                "title": "Missing machine-explicit Organization entity",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "The brand publishes no Schema.org Organization markup, leading to machine ambiguity.",
                "cause_family": "ENTITY.IDENTITY",
                "id": "MATERIAL_ENTITY_AMBIGUITY",
                "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                "impact": "AI models cannot resolve the brand entity with high confidence, leading to entity collisions and ungrounded answers.",
                "evidence": f"No Schema.org Organization JSON-LD block detected on {base}/{og_note}.",
                "suggested_action": {
                    "summary": "Publish Organization JSON-LD markup declaring name, url, logo, and sameAs links.",
                    "technical_fix": "Deploy Organization JSON-LD with @type, name, url, logo, and sameAs links to official profiles.",
                    "creative_fix": "Clarify official brand name, founding year, and corporate mission in footer and about page copy.",
                    "priority": "medium",
                    "verification": "Inspect homepage JSON-LD and confirm Organization schema parses validly.",
                },
            }
        )
        recommendations.append(
            {
                "title": "Add Organization JSON-LD schema",
                "category": "entity-identity",
                "rationale": f"Brand '{brand_name}' lacks machine-explicit JSON-LD Organization markup.",
                "suggested_action": "Add an Organization JSON-LD block linking canonical brand name, logo, and authoritative sameAs profiles.",
            }
        )
    else:
        # Check for authoritative social profiles present in DOM but omitted from sameAs
        discovered_social = set()
        if inv and inv.get("pages"):
            for p in inv.get("pages", []):
                for sl in p.get("social_links", []):
                    m = re.search(r"https?://[^\s'\"\)]+", str(sl))
                    if m:
                        discovered_social.add(m.group(0).rstrip("/"))

        declared_sameas = set()
        s_raw = org_entity.get("sameAs") or []
        if isinstance(s_raw, str):
            s_raw = [s_raw]
        for s in s_raw:
            m = re.search(r"https?://[^\s'\"\)]+", str(s))
            if m:
                declared_sameas.add(m.group(0).rstrip("/").lower())

        unlinked_social = [
            sl for sl in sorted(discovered_social)
            if not any(sl.lower() == ds for ds in declared_sameas)
        ]
        if unlinked_social and not any(f.get("cause_id") == "MISSING_SAMEAS_VERIFICATION" for f in findings):
            clean_examples = unlinked_social[:5]
            findings.append(
                {
                    "category": "entity-identity",
                    "title": "Authoritative social profiles present in DOM but omitted from Organization sameAs",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "The site links to verified third-party social profiles in HTML but omits them from Schema.org Organization sameAs declarations.",
                    "cause_family": "ENTITY.IDENTITY",
                    "id": "MISSING_SAMEAS_VERIFICATION",
                    "cause_id": "MISSING_SAMEAS_VERIFICATION",
                    "impact": "AI models cannot establish bidirectional Knowledge Graph corroboration between the domain and official external entities.",
                    "evidence": f"Found on-page social profiles omitted from Organization sameAs: {', '.join(clean_examples)}",
                    "suggested_action": {
                        "summary": "Add discovered social profile URLs to the Organization sameAs array in JSON-LD.",
                        "technical_fix": f"Update Organization JSON-LD on homepage to include 'sameAs': {json.dumps(clean_examples)}.",
                        "creative_fix": "Ensure corporate marketing social profiles are maintained and aligned across all platforms.",
                        "priority": "medium",
                        "verification": "Inspect homepage JSON-LD and verify sameAs links match external brand profiles.",
                    },
                }
            )

    # 3. Answerability Evaluation Across Sampled HTML Pages (Excluding Homepage)
    answerability_evaluations = []
    for p in html_pages:
        ptype = p.get("page_type")
        phtml = p.get("html")
        purl = p.get("url")
        ans = None
        if ptype in MATERIAL_ATTRIBUTE_WEIGHTS and ptype != "homepage" and phtml:
            pdom = EntityDOMParser()
            try:
                pdom.feed(phtml)
            except Exception:
                pass
            typed_objects = parse_json_ld(pdom.json_ld_contents, phtml)
            ans = evaluate_page_answerability(ptype, phtml, pdom, purl, typed_objects, page_dict=p)
            if isinstance(ans, dict) and ans.get("status") == "missing_entity":
                # Commercial product/catalog route completely missing Product schema
                if not any(f.get("cause_id") == "ATTRIBUTE_INCOMPLETENESS" and purl in str(f.get("evidence", "")) for f in findings):
                    findings.append(
                        {
                            "category": "product-answerability",
                            "title": f"No Schema.org Product structured data on {ptype.replace('_', ' ')} page",
                            "severity": "high",
                            "confidence": "high",
                            "root_cause": f"MISSING_PRODUCT_SCHEMA: Commercial {ptype.replace('_', ' ')} page on {purl} publishes no Schema.org Product or ItemList JSON-LD structured data.",
                            "cause_family": "ENTITY.ATTRIBUTE_INCOMPLETENESS",
                            "id": "ATTRIBUTE_INCOMPLETENESS",
                            "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                            "url": purl,
                            "scope": purl,
                            "impact": "Generative shopping assistants (ChatGPT Instant Checkout, Perplexity Shopping, Google Shopping Graph) cannot resolve product catalog items, prices, or inventory status.",
                            "evidence": f"Commercial route {purl} contains 0 Schema.org Product or ItemList entities in JSON-LD.",
                            "suggested_action": {
                                "summary": f"Deploy Schema.org Product markup on {purl}.",
                                "technical_fix": "Embed Schema.org Product JSON-LD declaring name, description, offers with clean numeric price and ISO 4217 priceCurrency, and inStock availability.",
                                "creative_fix": "Ensure visible product catalog titles, pricing, and availability are presented in semantic HTML above the fold.",
                                "priority": "high",
                                "verification": f"Validate {purl} with Schema.org Validator or Google Rich Results Test to confirm Product markup is detected.",
                            },
                        }
                    )
            elif isinstance(ans, dict) and ans.get("status") == "present":
                results_list = ans.get("results")
                if isinstance(results_list, list):
                    for res in results_list:
                        if isinstance(res, dict):
                            answerability_evaluations.append(res)
                            res_facts = res.get("facts")
                            if isinstance(res_facts, dict):
                                missing = [k for k, v in res_facts.items() if not v]
                                if missing:
                                    is_prod = ptype in ("product_detail", "product")
                                    cat_name = "product-answerability" if is_prod else f"{ptype.replace('_', '-')}-answerability"
                                    ptype_disp = ptype.replace('_', ' ')
                                    t_title = (
                                        f"Product Schema missing critical Answerability attributes ({', '.join(missing)})"
                                        if is_prod
                                        else f"{ptype_disp.title()} page missing critical Answerability attributes ({', '.join(missing)})"
                                    )
                                    findings.append(
                                        {
                                            "category": cat_name,
                                            "title": t_title,
                                            "severity": "medium",
                                            "confidence": "high",
                                            "root_cause": (
                                                f"The Product JSON-LD block on {purl} omits facts required by AI shopping assistants."
                                                if is_prod
                                                else f"The {ptype_disp} page on {purl} omits material attributes required by AI search engines: {', '.join(missing)}."
                                            ),
                                            "cause_family": "ENTITY.ATTRIBUTE_INCOMPLETENESS",
                                            "id": "ATTRIBUTE_INCOMPLETENESS",
                                            "cause_id": "ATTRIBUTE_INCOMPLETENESS",
                                            "url": purl,
                                            "scope": purl,
                                            "impact": (
                                                "AI assistants (e.g. ChatGPT Search, Perplexity Shopping) may refuse to recommend the product due to missing pricing or stock status."
                                                if is_prod
                                                else f"AI retrieval engines cannot reliably answer user queries regarding {ptype_disp} due to missing {', '.join(missing)}."
                                            ),
                                            "evidence": (
                                                f"Product JSON-LD on {purl} lacks: {', '.join(missing)}. Current score: {res.get('score', 0.0)}/1.0."
                                                if is_prod
                                                else f"{ptype_disp.title()} on {purl} lacks material facts: {', '.join(missing)}. Current answerability score: {res.get('score', 0.0)}/1.0."
                                            ),
                                            "suggested_action": {
                                                "summary": (
                                                    f"Add {', '.join(missing)} to the Product JSON-LD schema."
                                                    if is_prod
                                                    else f"Add missing material attributes ({', '.join(missing)}) to {purl}."
                                                ),
                                                "technical_fix": (
                                                    f"Enrich Product JSON-LD with missing attributes ({', '.join(missing)}) under offers and specifications."
                                                    if is_prod
                                                    else f"Enrich {ptype_disp} markup and JSON-LD with missing attributes: {', '.join(missing)}."
                                                ),
                                                "creative_fix": (
                                                    "Display visible pricing, availability, and product attributes in clear editorial tables adjacent to purchase CTAs."
                                                    if is_prod
                                                    else f"Display clear editorial and structured information for {', '.join(missing)} on the {ptype_disp} page."
                                                ),
                                                "priority": "medium",
                                                "verification": (
                                                    "Check the Google Rich Results Test to confirm the properties are populated."
                                                    if is_prod
                                                    else f"Validate {purl} with Schema.org Validator to confirm structured data and material facts are correctly declared."
                                                ),
                                            },
                                        }
                                    )

            # 3.1 Google Deprecated Schema Check (from schema_ecommerce_validate.py)
            deprecated_types = {
                "vehicle": "Vehicle Listing rich result retired by Google.",
                "vehiclelisting": "Vehicle Listing rich result retired by Google.",
                "claimreview": "Claim Review rich result retired by Google.",
                "estimatedsalary": "Estimated Salary rich result retired by Google.",
                "learningvideo": "Learning Video rich result retired by Google.",
                "specialannouncement": "Special Announcement rich result deprecated by Google.",
                "practiceproblem": "Practice Problem rich result retired by Google (January 2026).",
                "bookactions": "Book Actions rich result retired by Google.",
                "courseinfo": "Course Info rich result retired by Google.",
            }
            for obj in typed_objects:
                t_raw = obj.get("@type", "")
                types_to_check = t_raw if isinstance(t_raw, list) else [t_raw]
                for t in types_to_check:
                    if isinstance(t, str) and t.lower() in deprecated_types:
                        findings.append(
                            {
                                "category": "schema-deprecation",
                                "title": f"Declared Schema.org type '{t}' is retired by search engines",
                                "severity": "medium",
                                "confidence": "high",
                                "root_cause": f"SCHEMA_DEPRECATION: Schema type '{t}' was retired in search engine rich results updates.",
                                "cause_family": "ENTITY.IDENTITY",
                                "id": "SCHEMA_DEPRECATION",
                                "cause_id": "SCHEMA_DEPRECATION",
                                "impact": "Search and generative AI engines ignore retired structured data types, failing to generate enhanced knowledge panel features.",
                                "evidence": f"Page {purl} declares retired type '{t}'. {deprecated_types[t.lower()]}",
                                "suggested_action": {
                                    "summary": f"Migrate or remove deprecated '{t}' schema from {purl}.",
                                    "technical_fix": f"Replace '{t}' with modern standard Schema.org types (e.g. Product, VideoObject, Organization).",
                                    "creative_fix": "Audit structured data markup against current search documentation.",
                                    "priority": "medium",
                                    "verification": "Confirm Google Rich Results Test passes without deprecation warnings.",
                                },
                            }
                        )

            # Rule SC01 & SC02: Clean Float Price, ISO 4217, and sameAs Density
            for obj in typed_objects:
                # SC01: sameAs profile density
                if matches_schema_type(obj, ("organization", "corporation")):
                    same_as = obj.get("sameAs", [])
                    same_as_list = same_as if isinstance(same_as, list) else [same_as]
                    if len(same_as_list) < 2:
                        recommendations.append(
                            {
                                "id": "PROACTIVE.ENTITY.SAMEAS_DENSITY.001",
                                "title": "Declare at least two authoritative sameAs profile links in Organization schema",
                                "category": "entity",
                                "summary": f"Organization schema on {purl} declares {len(same_as_list)} sameAs link(s). Linking to >= 2 verified external identity anchors (Wikidata, Wikipedia, LinkedIn, GitHub) is required for definitive Knowledge Graph entity resolution.",
                                "priority": "medium",
                                "technical_fix": "Add verified Wikidata, LinkedIn, or official social profile URLs to the sameAs array.",
                                "creative_fix": "Ensure corporate profiles on major authority platforms link back canonically to the brand.",
                                "verification": "Verify sameAs array contains >= 2 valid authority URLs.",
                            }
                        )
                # SC02: Offer clean float price
                if matches_schema_type(obj, ("product", "individualproduct", "offer")):
                    offers_raw = obj.get("offers", obj if matches_schema_type(obj, ("offer",)) else {})
                    offers_items = offers_raw if isinstance(offers_raw, list) else [offers_raw]
                    for off in offers_items:
                        if isinstance(off, dict):
                            price_val = off.get("price")
                            if (
                                price_val is not None
                                and isinstance(price_val, str)
                                and any(sym in price_val for sym in ("$", "€", "£", "¥"))
                            ):
                                findings.append(
                                    {
                                        "category": "entity",
                                        "title": "Offer price contains currency symbol (must be clean float)",
                                        "severity": "medium",
                                        "confidence": "high",
                                        "root_cause": f"SCHEMA_PRICE_FORMAT_INVALID: Offer price '{price_val}' on {purl} contains currency symbols. AI buying agents and Google Merchant specifications require price to be a clean numeric string (e.g. '49.00', not '$49.00').",
                                        "cause_family": "COMMERCIAL.TRANSACTION_GAP",
                                        "id": "SCHEMA_PRICE_FORMAT_INVALID",
                                        "cause_id": "SCHEMA_PRICE_FORMAT_INVALID",
                                        "evidence": f"Offer declared price as '{price_val}'. Currency must be isolated in priceCurrency.",
                                        "impact": "Autonomous procurement and shopping agents fail to parse numerical pricing, excluding the product from AI shopping results.",
                                        "suggested_action": {
                                            "summary": "Strip currency symbols from price and declare ISO 4217 in priceCurrency.",
                                            "technical_fix": "Format schema price as 'price': '49.00' and 'priceCurrency': 'USD'.",
                                            "creative_fix": "Display currency symbols visually in HTML while keeping JSON-LD numeric.",
                                            "priority": "medium",
                                            "verification": "Confirm price contains only digits and decimal points.",
                                        },
                                    }
                                )

            # Rule HF-06 & W-03: Product Consistency (HTML text vs JSON-LD Offer Price)
            for obj in typed_objects:
                if matches_schema_type(obj, ("product", "individualproduct")):
                    offers = obj.get("offers", {})
                    offer_items = offers if isinstance(offers, list) else [offers]
                    for off in offer_items:
                        if isinstance(off, dict):
                            schema_price_raw = str(off.get("price", ""))
                            # Extract visible price from HTML text
                            html_prices = re.findall(r"[$]\s*(\d+(?:\.\d{2})?)", phtml)
                            if html_prices and schema_price_raw:
                                # Clean schema price
                                clean_schema_price = re.sub(r"[^0-9.]", "", schema_price_raw)
                                if clean_schema_price and clean_schema_price not in html_prices:
                                    findings.append(
                                        {
                                            "category": "commercial",
                                            "title": "Product price contradiction between HTML copy and JSON-LD (HF-06)",
                                            "severity": "critical",
                                            "confidence": "high",
                                            "root_cause": f"COMMERCIAL_PRODUCT_DATA_CONTRADICTION: HTML copy displays price(s) '${html_prices[0]}' but JSON-LD Offer declares price '{schema_price_raw}'. Autonomous shopping agents and Google Merchant Graph drop product trust on data contradictions.",
                                            "cause_family": "COMMERCIAL.TRANSACTION_GAP",
                                            "id": "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
                                            "cause_id": "COMMERCIAL_PRODUCT_DATA_CONTRADICTION",
                                            "evidence": f"HTML price: ${html_prices[0]} vs JSON-LD price: {schema_price_raw} on {purl}.",
                                            "impact": "AI shopping assistants (ChatGPT Instant Checkout, Google Shopping Graph) reject contradictory product offers.",
                                            "suggested_action": {
                                                "summary": "Synchronize HTML visible pricing with JSON-LD Offer price.",
                                                "technical_fix": f"Update JSON-LD Offer price to match verified visible price of {html_prices[0]}.",
                                                "creative_fix": "Implement single-source-of-truth pricing rendering on product detail pages.",
                                                "priority": "critical",
                                                "verification": "Confirm HTML and JSON-LD offer prices match exactly.",
                                            },
                                        }
                                    )

            # Rule UCP-01 & A2A-01: Universal Commerce Protocol & Agent2Agent Interoperability Probes
            if inv:
                infra = inv.get("infrastructure", {})
                has_ucp = bool(infra.get("ucp_manifest"))
                has_a2a = bool(infra.get("a2a_agent_card"))
                if (
                    not has_ucp
                    and not has_a2a
                    and any(p.get("page_type") in ("product", "pricing") for p in html_pages)
                ):
                    recommendations.append(
                        {
                            "id": "PROACTIVE.COMMERCE.AGENTIC_PROTOCOL.001",
                            "title": "Implement Universal Commerce Protocol (UCP) or A2A agent cards for autonomous checkout",
                            "category": "commercial",
                            "summary": "The site lacks machine-readable agentic commerce protocols (Google UCP, Agent Payments AP2, or Agent2Agent A2A). Emerging AI buying agents (Gemini AI Mode, ChatGPT Checkout) require programmatic discovery and checkout manifests.",
                            "priority": "medium",
                            "technical_fix": "Expose a machine-readable commerce manifest at '/.well-known/ucp.json' or 'agent_card.json' declaring cart, checkout, and inventory capabilities.",
                            "creative_fix": "Publish an OpenAPI specification defining transactional endpoints for purchasing agents.",
                            "verification": "Verify GET /.well-known/ucp.json returns HTTP 200 with valid schema.",
                        }
                    )

            # 3.2 Merchant Listing Return & Shipping Policies Check
            for obj in typed_objects:
                if matches_schema_type(obj, ("product", "individualproduct")):
                    offers = obj.get("offers", {})
                    if isinstance(offers, dict):
                        has_return = "hasMerchantReturnPolicy" in offers or "hasMerchantReturnPolicy" in obj
                        has_shipping = "shippingDetails" in offers or "shippingDetails" in obj
                        if not (has_return and has_shipping):
                            recommendations.append(
                                {
                                    "id": "PROACTIVE.ENTITY.MERCHANT_RETURN_SHIPPING.001",
                                    "title": "Add hasMerchantReturnPolicy and shippingDetails to Product Offer schema",
                                    "category": "entity-answerability",
                                    "summary": f"Product on {purl} declares pricing but omits merchant return policy and shipping details. Search engines and AI shopping assistants require explicit shipping and return terms for automated merchant listing eligibility.",
                                    "priority": "low",
                                    "technical_fix": "Add hasMerchantReturnPolicy and shippingDetails objects inside the Offer JSON-LD schema.",
                                    "creative_fix": "Clearly state shipping timeframes and return windows in human-readable policy blocks adjacent to pricing.",
                                    "verification": "Confirm Google Merchant Listing test recognizes valid return policy and shipping details.",
                                }
                            )

            # 3.3 Non-Text Fact Locking Check:
            # Detects critical commercial/pricing/specification charts locked inside unparsed raster images
            locked_images = []
            img_candidates = list(p.get("images", []))
            if not img_candidates and phtml:
                for im in re.finditer(r'<img\s+([^>]+)>', phtml, re.IGNORECASE):
                    attrs_str = im.group(1)
                    src_m = re.search(r'src=["\']([^"\']+)["\']', attrs_str, re.IGNORECASE)
                    alt_m = re.search(r'alt=["\']([^"\']*)["\']', attrs_str, re.IGNORECASE)
                    cls_m = re.search(r'class=["\']([^"\']+)["\']', attrs_str, re.IGNORECASE)
                    id_m = re.search(r'id=["\']([^"\']+)["\']', attrs_str, re.IGNORECASE)
                    img_candidates.append({
                        "src": src_m.group(1) if src_m else "",
                        "alt": alt_m.group(1) if alt_m else "",
                        "class": cls_m.group(1) if cls_m else "",
                        "id": id_m.group(1) if id_m else "",
                    })

            for im_obj in img_candidates:
                src_val = (im_obj.get("src") or "").lower()
                alt_val = (im_obj.get("alt") or "").strip().lower()
                cls_id_val = f"{im_obj.get('class', '')} {im_obj.get('id', '')}".lower()
                combined_img_str = f"{src_val} {cls_id_val}"

                is_commercial_img = bool(
                    re.search(
                        r"\b(pricing|price|tier|plan|comparison|spec|specification|features|menu|chart|infographic|rates|dimensions)\b",
                        combined_img_str,
                    )
                )
                is_unannotated_alt = not alt_val or len(alt_val) < 15 or alt_val in (
                    "pricing", "image", "chart", "table", "menu", "features", "infographic"
                )
                if is_commercial_img and is_unannotated_alt:
                    img_filename = src_val.split("/")[-1].split("?")[0] or "raster_graphic"
                    locked_images.append((img_filename, alt_val or "empty"))

            has_prod_schema = any(matches_schema_type(o, ("product", "individualproduct", "offer")) for o in typed_objects)
            has_html_table = bool(re.search(r"<table\b[^>]*>", phtml or "", re.IGNORECASE))

            if locked_images and not has_prod_schema and not has_html_table:
                sample_img, sample_alt = locked_images[0]
                findings.append(
                    {
                        "category": "entity-answerability",
                        "title": f"Key commercial facts locked in non-textual images without machine-readable schema on {purl}",
                        "severity": "high",
                        "confidence": "high",
                        "root_cause": f"MISSING_MATERIAL_FACT: Graphic charts ('{sample_img}') lock essential pricing and specification facts inside raster images without machine-readable Schema.org JSON-LD or semantic HTML table markup.",
                        "cause_family": "ENTITY.ANSWERABILITY",
                        "id": "MISSING_MATERIAL_FACT",
                        "cause_id": "MISSING_MATERIAL_FACT",
                        "impact": "Generative search engines (ChatGPT Search, Claude, Perplexity) cannot perform OCR during search indexing, resulting in total omission of commercial specifications in AI comparison cards.",
                        "evidence": f"Detected commercial graphic ('{sample_img}') with uninformative alt text ('{sample_alt}') on {purl}, with 0 Product/Offer JSON-LD schemas and 0 semantic HTML data tables present.",
                        "suggested_action": {
                            "summary": f"Extract pricing and specifications from '{sample_img}' into Schema.org Product/Offer JSON-LD and semantic HTML tables.",
                            "priority": "high",
                            "technical_fix": f"Deploy standard Schema.org Product/Offer JSON-LD representing the tiers and specifications shown in '{sample_img}', paired with an HTML5 <table>.",
                            "creative_fix": "Retain visual marketing infographics for human visitors while providing an identical machine-readable structured data layer for AI crawlers.",
                            "verification": "Confirm that search engine crawlers extract complete numeric prices and attributes without raster image processing.",
                        },
                    }
                )

    if state_file:
        if "entities" not in state:
            state["entities"] = {}
        for p in html_pages:
            if not isinstance(p, dict):
                continue
            u = p.get("url", "")
            if u not in state["entities"]:
                state["entities"][u] = []
            phtml = p.get("html", "")
            if phtml:
                pdom = EntityDOMParser()
                try:
                    pdom.feed(phtml)
                except Exception:
                    pass
                for o in parse_json_ld(pdom.json_ld_contents, phtml):
                    if isinstance(o, dict) and o.get("name") and o.get("name") not in state["entities"][u]:
                        state["entities"][u].append(o["name"])
            if brand_name and brand_name not in state["entities"][u]:
                state["entities"][u].append(brand_name)
        import tempfile

        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(state_file)))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, state_file)

    if answerability_only:
        return {
            "status": "ok",
            "answerability_evaluations": answerability_evaluations,
            "coverage": {
                "html_pages_evaluated": len(html_pages),
                "answerability_evaluations_count": len(answerability_evaluations),
            },
        }

    res_payload = {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "entity_snapshot": {
            "brand_name": brand_name,
            "organization": org_entity,
            "og_site_name": og_site_name,
            "title": dom.title,
        },
        "coverage": {
            "html_pages_evaluated": len(html_pages),
            "answerability_evaluations": answerability_evaluations,
            "json_ld_count": len(json_ld_entities),
            # Ratios for continuous orchestrator scoring (structured data completeness)
            "org_schema_pages": 1 if org_entity else 0,
            "product_schema_pages": sum(
                1 for p in html_pages
                if any(
                    "product" in str(e.get("@type", "")).lower()
                    for e in parse_json_ld(p.get("json_ld_contents", []), p.get("html", ""))
                )
            ) if len(html_pages) > 1 else (1 if any("product" in str(e.get("@type", "")).lower() for e in json_ld_entities) else 0),
            "total_pages": len(html_pages),
        },
        "limitations": [
            "Entity and answerability analysis was performed on sampled first-party HTML; authenticated portals were not evaluated."
        ],
    }

    if target_url:
        res_payload["target_inspection"] = inspect_target_entity(inv, base, domain, target_url)

    if schema_type:
        st_clean = schema_type.lower().strip()
        matched = []
        for p in html_pages:
            p_ents = parse_json_ld(p.get("json_ld_contents", []), p.get("html", ""))
            for e in p_ents:
                if isinstance(e, dict) and st_clean in str(e.get("@type", "")).lower():
                    matched.append({"url": p.get("url"), "entity": e})
        res_payload["matching_entities"] = matched

    return res_payload


def format_markdown_summary(res: Dict[str, Any], domain: Optional[str] = None) -> str:
    """Format entity content sensor result as clean, readable Markdown."""
    lines = [f"# Entity & Structured Data Diagnostic Report: {domain or 'Target Site'}"]
    lines.append(f"\n- **Status:** `{res.get('status', 'ok')}`")
    cov = res.get("coverage", {})
    if isinstance(cov, dict) and cov:
        lines.append(f"- **HTML Pages Evaluated:** {cov.get('html_pages_evaluated', 0)}")
        lines.append(f"- **Total JSON-LD Blocks:** {cov.get('total_json_ld_blocks', 0)}")
        lines.append(f"- **Schema Types Present:** {', '.join(cov.get('schema_types_present', [])) or 'None'}")
        lines.append(f"- **Answerability Index:** {cov.get('mean_answerability_score', 'N/A')}")

    findings = res.get("findings", [])
    lines.append(f"\n## Diagnostic Findings ({len(findings)})")
    if not findings:
        lines.append("\nNo entity resolution or schema defects detected.")
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

    recs = res.get("recommendations", [])
    if recs:
        lines.append(f"\n## Proactive Recommendations ({len(recs)})")
        for r in recs:
            lines.append(f"- **[{str(r.get('priority', 'medium')).upper()}] {r.get('id', 'REC')}:** {r.get('title', '')} - {r.get('summary', '')}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Entity Identity & Content Answerability Diagnostic Sensor.\n"
            "Evaluates Schema.org @graph architectures (Organization, WebSite, Product, Offer, "
            "services, contact), validates ISO 4217 priceCurrency codes, and computes the 7-attribute Answerability Index."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--inventory", help="Path to pre-crawled site inventory JSON (inv.json) for offline execution")
    parser.add_argument("--state", help="Path to global state JSON (optional multi-turn evaluation)")
    parser.add_argument("--url", help="Target specific route or URL for forensic entity and structured data inspection")
    parser.add_argument("--schema-type", dest="schema_type", help="Filter and inspect entities matching a specific Schema.org type (e.g. Product, Organization, Service)")
    parser.add_argument("--answerability-only", action="store_true", help="Emit only the 7-attribute Answerability Index evaluations")
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
        target_url=args.url,
        schema_type=args.schema_type,
        answerability_only=args.answerability_only,
    )
    if args.format == "markdown":
        print(format_markdown_summary(res, domain=p.netloc))
    else:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
