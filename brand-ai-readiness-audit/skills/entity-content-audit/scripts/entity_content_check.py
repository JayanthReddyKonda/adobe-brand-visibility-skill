#!/usr/bin/env python3
"""
entity_content_check.py - Entity identity & content answerability audit layer.

Causal Root Causes:
  - ENTITY.IDENTITY: MATERIAL_ENTITY_AMBIGUITY, WEAK_IDENTITY_SIGNALS
  - ENTITY.ANSWERABILITY: INCOMPLETE_OFFER_ATTRIBUTES, MISSING_MATERIAL_FACT, WEAK_ANSWER_SURFACE

Calculates the mathematically reproducible weighted Answerability Index:
  Index = sum(weight_i * present_i) / sum(weight_i)

Enforces strict Resource Invariant:
  - Only genuine HTML pages enter answerability audits (XML sitemaps and feeds are strictly excluded).
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



# Weighted Answerability Schema by Page Type (Structured & Measurable Material Attributes)
ANSWERABILITY_WEIGHTS = {
    "product_detail": {
        "product_name": (0.30, ["product", "item", "model", "sku", "title"]),
        "price": (0.25, ["₹", "$", "usd", "inr", "eur", "£", "price", "starts at", "/mo"]),
        "availability": (0.25, ["in stock", "available", "ships in", "out of stock", "pre-order", "schema.org/instock", "in_stock"]),
        "specifications": (0.20, ["specifications", "features", "origin", "weight", "capacity", "sla", "dimensions", "details"])
    },

    "product": {  # Alias for single product pages
        "product_name": (0.30, ["product", "item", "drone", "solution", "tool", "coffee", "roast", "blend", "model"]),
        "price": (0.25, ["₹", "$", "usd", "inr", "eur", "£", "price", "starts at", "/mo"]),
        "availability": (0.25, ["in stock", "available", "ships in", "out of stock", "pre-order", "schema.org/instock", "in_stock"]),
        "specifications": (0.20, ["specifications", "features", "origin", "weight", "capacity", "sla", "dimensions", "details"])
    },
    "product_listing": {
        "catalog_items": (0.40, ["products", "items", "browse", "catalog", "shop", "collection", "filter"]),
        "category_title": (0.30, ["category", "all products", "our products", "shop all", "catalog", "explore"]),
        "action_path": (0.30, ["view", "buy", "details", "add to cart", "shop now", "order"])
    },
    "category": {
        "catalog_items": (0.40, ["products", "items", "browse", "catalog", "shop", "collection", "filter"]),
        "category_title": (0.30, ["category", "all products", "our products", "shop all", "catalog", "explore"]),
        "action_path": (0.30, ["view", "buy", "details", "add to cart", "shop now", "order"])
    },
    "subscription_flow": {
        "plan_description": (0.35, ["subscription", "club", "membership", "recurring", "monthly", "deliveries", "frequency"]),
        "selection_options": (0.35, ["choose", "select", "options", "beans", "grind", "frequency", "tier", "plan"]),
        "cta_action": (0.30, ["subscribe", "join", "sign up", "start", "checkout", "get started"])
    },
    "pricing": {
        "tier_names": (0.35, ["starter", "pro", "enterprise", "basic", "premium", "tier", "plan", "membership"]),
        "price_figures": (0.35, ["₹", "$", "usd", "inr", "eur", "£", "/mo", "/month", "/year", "free", "contact sales"]),
        "feature_comparison": (0.30, ["features", "includes", "comparison", "unlimited", "storage", "users", "benefits"])
    },
    "service": {
        "service_name": (0.40, ["service", "consulting", "managed", "solution", "offerings"]),
        "deliverables": (0.30, ["deliverables", "capabilities", "scope", "includes", "what we do"]),
        "engagement_model": (0.30, ["hourly", "retainer", "fixed", "timeline", "process", "contact"])
    },
    "contact": {
        "email_channel": (0.40, ["@", "mailto:", "support@", "sales@", "contact@", "email"]),
        "phone_channel": (0.30, ["tel:", "+", "call", "phone", "hotline"]),
        "location_or_form": (0.30, ["street", "address", "suite", "floor", "city", "headquarters", "form", "send message", "message"])
    }
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
        elif not self.in_script:
            if data.strip():
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


def parse_json_ld(raw_json_list):
    """Extract Schema.org typed objects and resolve decoupled @graph node references (@id linking)."""
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
                entity["offers"] = [id_map.get(o["@id"], o) if isinstance(o, dict) and "@id" in o and o["@id"] in id_map else o for o in offers]

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



def evaluate_page_answerability(page_type, html_content, dom, url):
    """Calculate mathematically reproducible weighted Answerability Index."""
    weights_map = ANSWERABILITY_WEIGHTS.get(page_type)
    if not weights_map:
        return None

    full_text = " ".join(dom.text_content)
    headings_text = " ".join(h[1] for h in dom.headings)
    search_space = f"{full_text} {headings_text}"

    present_attributes = []
    missing_attributes = []
    earned_weight = 0.0
    total_weight = sum(w for w, _ in weights_map.values())

    for attr_name, (weight, patterns) in weights_map.items():
        found = False
        for pat in patterns:
            # Word boundary regex search to prevent substring pollution
            if re.search(r'\b' + re.escape(pat) + r'\b', search_space, re.I) or (len(pat) > 3 and pat.lower() in search_space.lower()):
                found = True
                break
        if found:
            present_attributes.append(attr_name)
            earned_weight += weight
        else:
            missing_attributes.append(attr_name)

    coverage_ratio = round(earned_weight / total_weight, 2) if total_weight > 0 else 1.0

    return {
        "page_type": page_type,
        "url": url,
        "coverage_ratio": coverage_ratio,
        "present": present_attributes,
        "missing": missing_attributes,
        "weights": {k: v[0] for k, v in weights_map.items()}
    }


def audit(base, domain, inv=None):
    findings, recommendations, observations = [], [], []

    # 1. Filter genuine HTML pages from inventory
    html_pages = []
    if inv is not None:
        for p in inv.get("pages", []):
            u = p.get("url", "")
            raw_html = p.get("html", "")
            # Strict non-HTML / sitemap rejection
            if u.lower().endswith((".xml", ".xml.gz", ".txt", ".json", ".pdf")):
                continue
            if raw_html.strip().startswith("<?xml") or "<urlset" in raw_html.lower() or "<sitemapindex" in raw_html.lower():
                continue
            if p.get("resource_type") == "html" or "<html" in raw_html.lower() or "<!doctype html" in raw_html.lower() or p.get("page_type") == "homepage":
                html_pages.append(p)
    else:
        status, html, headers, _ = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if html:
            html_pages.append({
                "url": base + "/",
                "status": status,
                "resource_type": "html",
                "page_type": "homepage",
                "html": html
            })

    if not html_pages:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not reach {base} or no HTML pages found"
        }

    home_page = next((p for p in html_pages if p.get("page_type") == "homepage"), html_pages[0])
    home_html = home_page.get("html", "")

    dom = EntityDOMParser()
    try:
        dom.feed(home_html)
    except Exception:
        pass

    json_ld_entities = parse_json_ld(dom.json_ld_contents)

    # 2. Organization Entity Recognition (supports array @type)
    org_entity = None
    for e in json_ld_entities:
        if matches_schema_type(e, ("organization", "corporation", "brand", "localbusiness")):
            org_entity = e
            break

    og_site_name = dom.og_tags.get("og:site_name")
    brand_name = (org_entity.get("name") if org_entity and isinstance(org_entity.get("name"), str) else None) or og_site_name or dom.title.split("-")[0].split("|")[0].strip()

    if not org_entity:
        if not og_site_name and not dom.title:
            findings.append({
                "category": "entity-identity",
                "title": "Missing machine-explicit Organization entity",
                "severity": "medium",

                "confidence": "high",
                "root_cause": "The brand publishes no Schema.org Organization markup, OpenGraph site_name, or descriptive title.",
                "cause_family": "ENTITY.IDENTITY",
                "cause_id": "MATERIAL_ENTITY_AMBIGUITY",
                "impact": "AI models cannot resolve the brand entity with high confidence, leading to entity collisions and ungrounded answers.",
                "evidence": f"No JSON-LD Organization block or og:site_name found on {base}/.",
                "suggested_action": {
                    "summary": "Publish Organization JSON-LD markup declaring name, url, logo, and sameAs links.",
                    "priority": "medium",
                    "verification": "Inspect homepage JSON-LD and confirm Organization schema parses validly."
                }
            })
        else:
            recommendations.append({
                "title": "Add Organization JSON-LD schema",
                "category": "entity-identity",
                "rationale": f"Brand '{brand_name}' is stated in human-readable text but lacks machine-explicit JSON-LD Organization markup.",
                "suggested_action": "Add an Organization JSON-LD block linking canonical brand name, logo, and authoritative sameAs profiles."
            })

    # 3. Answerability Evaluation Across Sampled HTML Pages (Excluding Homepage)
    answerability_evaluations = []
    for p in html_pages:
        ptype = p.get("page_type")
        phtml = p.get("html")
        purl = p.get("url")
        if ptype in ANSWERABILITY_WEIGHTS and ptype != "homepage" and phtml:
            pdom = EntityDOMParser()
            try:
                pdom.feed(phtml)
            except Exception:
                pass
            ans = evaluate_page_answerability(ptype, phtml, pdom, purl)
            if ans:
                answerability_evaluations.append(ans)
                if ans["coverage_ratio"] < 0.60:
                    findings.append({
                        "category": "answerability",
                        "title": f"Low factual answerability on {ptype} page ({purl})",
                        "severity": "low",
                        "confidence": "medium",
                        "root_cause": f"The {ptype} page omits core factual attributes: {', '.join(ans['missing'])}.",
                        "cause_family": "ENTITY.ANSWERABILITY",
                        "cause_id": "MISSING_MATERIAL_FACT",
                        "impact": "AI assistants querying for specific commercial terms cannot locate direct answers on this surface.",
                        "evidence": f"Page covers only {int(ans['coverage_ratio']*100)}% of expected {ptype} facts. Missing: {', '.join(ans['missing'])}.",
                        "suggested_action": {
                            "summary": f"Expose missing {ptype} attributes ({', '.join(ans['missing'])}) in both visible body text and structured markup.",
                            "priority": "low",
                            "verification": f"Verify {purl} publishes explicit values for {', '.join(ans['missing'])}."
                        }
                    })

    # Calculate overall answerability index across evaluated pages
    if answerability_evaluations:
        avg_index = round(sum(a["coverage_ratio"] for a in answerability_evaluations) / len(answerability_evaluations), 2)
    else:
        avg_index = 1.0

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "entity_snapshot": {
            "brand_name": brand_name,
            "organization": org_entity,
            "og_site_name": og_site_name,
            "title": dom.title
        },
        "coverage": {
            "html_pages_evaluated": len(html_pages),
            "answerability_index": avg_index,
            "answerability_evaluations": answerability_evaluations,
            "json_ld_count": len(json_ld_entities)
        },
        "limitations": [
            "Entity and answerability analysis was performed on sampled first-party HTML; authenticated portals were not evaluated."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Entity & content understanding audit layer.")
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
