#!/usr/bin/env python3
"""
entity_content_check.py - Entity & content understanding layer.

Extracts first-party entity structures (Organization, Products, Offers, Services)
and evaluates whether an AI system can understand WHO the brand is and WHAT it offers.
Implements the Answerability Engine: measures the availability of essential factual
attributes across page types. Structured data absence is treated as an extractability
opportunity (recommendation), while malformed/conflicting markup is a finding.
"""
import sys
import os
import re
import json
import argparse
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audit-orchestrator", "scripts")))
    from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT
except ImportError:
    import urllib.request, urllib.error
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"
    def safe_fetch(url, timeout=10, max_bytes=2*1024*1024, user_agent=DEFAULT_USER_AGENT, method="GET"):
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(max_bytes).decode("utf-8", "ignore"), dict(r.headers), None
        except urllib.error.HTTPError as e:
            try:
                body = e.read(max_bytes).decode("utf-8", "ignore")
            except Exception:
                body = ""
            return e.code, body, dict(e.headers or {}), str(e)
        except Exception as e:
            return None, "", {}, str(e)

PRICE_PATTERN = re.compile(r'(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?(\d[\d,]*(?:\.\d{1,2})?)', re.IGNORECASE)
EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
PHONE_PATTERN = re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,4}\d{2,4}')


class EntityDOMParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.skip_depth = 0
        self.in_title = False
        self.title = ""
        self.meta_tags = {}
        self.og_tags = {}
        self.json_ld = []
        self.in_json_ld = False
        self.headings = []
        self.current_h = None
        self.current_h_text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = tag.lower()
        if t in ("script", "style", "noscript"):
            self.skip_depth += 1
            if t == "script" and "ld+json" in (a.get("type") or "").lower():
                self.in_json_ld = True
        elif t == "title":
            self.in_title = True
        elif t == "meta":
            prop = a.get("property") or a.get("name") or ""
            content = a.get("content") or ""
            if prop:
                self.meta_tags[prop.lower()] = content
                if prop.lower().startswith("og:"):
                    self.og_tags[prop.lower()] = content
        elif t in ("h1", "h2", "h3"):
            self.current_h = t
            self.current_h_text = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style", "noscript"):
            if self.skip_depth > 0:
                self.skip_depth -= 1
            if t == "script":
                self.in_json_ld = False
        elif t == "title":
            self.in_title = False
        elif t in ("h1", "h2", "h3"):
            if self.current_h:
                htext = " ".join(self.current_h_text).strip()
                if htext:
                    self.headings.append((self.current_h, htext))
            self.current_h = None

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld.append(data)
        elif self.in_title:
            self.title += data.strip()
        elif self.current_h is not None:
            self.current_h_text.append(data.strip())
        elif self.skip_depth == 0 and data.strip():
            self.text.append(data.strip())


def extract_structured_entities(json_ld_list, og_tags, title, base_url):
    """Extract Organization, Product, and Service entities from JSON-LD and OpenGraph."""
    org = {
        "name": og_tags.get("og:site_name") or None,
        "logo": og_tags.get("og:image") or None,
        "type": None,
        "same_as": [],
        "description": og_tags.get("og:description") or None,
    }
    products = []
    services = []
    dates = []

    for raw in json_ld_list:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            objs = data["@graph"]

        for o in objs:
            if not isinstance(o, dict):
                continue
            otype = str(o.get("@type", "")).lower()

            if otype in ("organization", "brand", "corporation", "localbusiness", "store"):
                org["type"] = o.get("@type")
                org["name"] = o.get("name") or org["name"]
                logo_val = o.get("logo")
                if isinstance(logo_val, dict):
                    org["logo"] = logo_val.get("url") or org["logo"]
                elif isinstance(logo_val, str):
                    org["logo"] = logo_val
                org["description"] = o.get("description") or org["description"]
                sa = o.get("sameAs") or []
                sa_list = sa if isinstance(sa, list) else [sa]
                for s in sa_list:
                    if isinstance(s, str) and s.startswith("http"):
                        org["same_as"].append(s)

            elif otype in ("product", "individualproduct"):
                offers = o.get("offers") or {}
                offer_obj = offers[0] if isinstance(offers, list) and offers else offers
                price = None
                currency = None
                avail = None
                if isinstance(offer_obj, dict):
                    price = offer_obj.get("price") or offer_obj.get("lowPrice")
                    currency = offer_obj.get("priceCurrency")
                    avail = offer_obj.get("availability")
                    if isinstance(avail, str) and "/" in avail:
                        avail = avail.split("/")[-1]

                brand_val = o.get("brand")
                brand_name = brand_val.get("name") if isinstance(brand_val, dict) else (brand_val if isinstance(brand_val, str) else None)

                products.append({
                    "name": o.get("name"),
                    "description": o.get("description"),
                    "brand": brand_name,
                    "price": str(price) if price is not None else None,
                    "currency": currency,
                    "availability": avail,
                    "sku": o.get("sku"),
                })

            elif otype in ("service", "financialservice", "professionalservice"):
                services.append({
                    "name": o.get("name"),
                    "service_type": o.get("serviceType"),
                    "description": o.get("description"),
                    "provider": o.get("provider", {}).get("name") if isinstance(o.get("provider"), dict) else o.get("provider")
                })

            if "dateModified" in o or "datePublished" in o:
                dates.append(o.get("dateModified") or o.get("datePublished"))

    if not org["name"] and title:
        # Fallback to title segment
        clean_title = title.split("|")[0].split("-")[0].strip()
        if clean_title:
            org["name"] = clean_title

    org["same_as"] = sorted(set(org["same_as"]))
    return org, products, services, dates


def evaluate_page_answerability(page_type, html_text, dom, base_url):
    """Deep inspection of expected material attributes for a page type."""
    text_lower = html_text.lower()
    headings_text = " ".join(t for _, t in dom.headings).lower()
    
    # Required core facts per page type
    EXPECTED_ATTRS = {
        "product": ["product_name", "price", "availability", "description", "brand_identity"],
        "pricing": ["pricing_tiers", "numeric_price", "currency", "plan_features"],
        "service": ["service_name", "deliverables", "contact_cta"],
        "location": ["physical_address", "operating_hours", "contact_phone"],
        "documentation": ["topic_heading", "implementation_example", "api_or_commands"],
        "contact": ["email_or_form", "phone_number", "company_identity"],
    }

    expected = EXPECTED_ATTRS.get(page_type)
    if not expected:
        return None

    present = []
    facts_discovered = {}

    if page_type == "product":
        if dom.headings or dom.title:
            present.append("product_name")
            facts_discovered["product_name"] = dom.headings[0][1] if dom.headings else dom.title
        prices = PRICE_PATTERN.findall(html_text)
        if prices:
            present.append("price")
            facts_discovered["price"] = prices[0]
        if any(w in text_lower for w in ("in stock", "out of stock", "pre-order", "availability", "add to cart", "buy now")):
            present.append("availability")
            facts_discovered["availability"] = "detected in text/controls"
        if len(dom.text) >= 40:
            present.append("description")
        if dom.og_tags.get("og:site_name") or dom.title:
            present.append("brand_identity")

    elif page_type == "pricing":
        prices = PRICE_PATTERN.findall(html_text)
        if prices:
            present.append("numeric_price")
            facts_discovered["price_sample"] = prices[:3]
        if any(w in text_lower for w in ("$", "₹", "rs", "eur", "usd", "gbp", "£", "€")):
            present.append("currency")
        if any(w in text_lower for w in ("tier", "plan", "monthly", "annually", "starter", "pro", "enterprise", "free")):
            present.append("pricing_tiers")
        if any(w in text_lower for w in ("features", "included", "unlimited", "storage", "users", "support")):
            present.append("plan_features")

    elif page_type == "service":
        if dom.headings:
            present.append("service_name")
        if any(w in text_lower for w in ("we provide", "offer", "deliver", "capabilities", "solutions", "services")):
            present.append("deliverables")
        if any(w in text_lower for w in ("contact", "get in touch", "book", "consultation", "request a quote")):
            present.append("contact_cta")

    elif page_type == "location":
        if any(w in text_lower for w in ("street", "suite", "road", "ave", "city", "pincode", "zip", "address", "floor")):
            present.append("physical_address")
        if any(w in text_lower for w in ("hours", "monday", "friday", "am", "pm", "open daily")):
            present.append("operating_hours")
        if PHONE_PATTERN.search(html_text):
            present.append("contact_phone")

    elif page_type == "documentation":
        if dom.headings:
            present.append("topic_heading")
        if any(w in text_lower for w in ("example", "curl", "python", "npm", "pip", "git", "function", "api", "$ ")):
            present.append("implementation_example")
            present.append("api_or_commands")

    elif page_type == "contact":
        if EMAIL_PATTERN.search(html_text) or "form" in text_lower:
            present.append("email_or_form")
        if PHONE_PATTERN.search(html_text):
            present.append("phone_number")
        if dom.title or dom.og_tags.get("og:site_name"):
            present.append("company_identity")

    missing = sorted(set(expected) - set(present))
    coverage_ratio = round(len(present) / len(expected), 2)

    return {
        "page_type": page_type,
        "expected": expected,
        "present": sorted(set(present)),
        "missing": missing,
        "coverage_ratio": coverage_ratio,
        "facts_sample": facts_discovered
    }


def audit(base, domain, inv=None):
    """Entity & content understanding audit."""
    findings, recommendations = [], []
    observations, limitations = [], []

    if inv is not None:
        home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
        if not home or not home.get("html"):
            return {"status": "inconclusive", "findings": [], "recommendations": [],
                    "error": "inventory lacks a usable homepage snapshot"}
        status, html = home["status"], home["html"]
        inv_pages = [p for p in inv.get("pages", []) if p.get("html") and p.get("page_type") != "homepage"]
    else:
        status, html, _, err = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        inv_pages = []

    if status is None:
        return {"status": "inconclusive", "findings": [], "recommendations": [],
                "error": f"could not reach {base}"}

    dom = EntityDOMParser()
    try:
        dom.feed(html)
    except Exception:
        pass

    full_text = " ".join(dom.text)
    words = len(full_text.split())
    org, products, services, dates = extract_structured_entities(dom.json_ld, dom.og_tags, dom.title, base)

    # 1. Organization Identity Explicitness
    identity_score = sum(1 for x in (org["name"], org["logo"], org["type"]) if x is not None)
    if identity_score == 0:
        findings.append(dict(
            category="entity-integrity",
            title="Organization identity is not machine-explicit",
            severity="medium",
            confidence="high",
            root_cause="No Organization/Brand JSON-LD, OpenGraph site_name, or extractable <title> brand identifier exists on the landing page.",
            cause_family="ENTITY.IDENTITY",
            cause_id="ENT-ORG-IDENTITY-MISSING",
            impact="AI assistants cannot reliably disambiguate the brand entity against similarly named companies.",
            evidence=f"Homepage ({base}/) carries {words} words but yields zero explicit Organization/Brand schema or og:site_name metadata.",
            suggested_action=dict(
                summary="Publish Organization JSON-LD markup declaring name, logo, legalName, url, and sameAs links.",
                priority="medium",
                verification="Re-fetch homepage and verify Organization JSON-LD parses with name and logo.")))

    # 2. Product / Offer Completeness
    if products:
        for p in products:
            missing_fields = []
            if not p.get("price"):
                missing_fields.append("price")
            if not p.get("availability"):
                missing_fields.append("availability")
            if not p.get("description"):
                missing_fields.append("description")

            if missing_fields:
                findings.append(dict(
                    category="content-quality",
                    title=f"Product markup for '{p.get('name') or 'Unnamed Product'}' is incomplete",
                    severity="low",
                    confidence="high",
                    root_cause="Product JSON-LD is published but omits material commercial fields.",
                    cause_family="ENTITY.ANSWERABILITY",
                    cause_id="ENT-PRODUCT-FIELDS-INCOMPLETE",
                    impact="AI assistants cannot quote authoritative pricing or availability, leading to hallucinated or omitted facts.",
                    evidence=f"Product schema on {base}/ omits material fields: {', '.join(missing_fields)}.",
                    suggested_action=dict(
                        summary=f"Populate missing Product schema fields ({', '.join(missing_fields)}) in JSON-LD.",
                        priority="low",
                        verification="Validate Product schema against Schema.org requirements.")))
    else:
        # Check if products exist in prose without markup
        prices_in_prose = PRICE_PATTERN.findall(full_text)
        if prices_in_prose:
            recommendations.append(dict(
                title="Publish structured Product / Offer JSON-LD",
                category="entity-clarity",
                rationale=f"Found {len(prices_in_prose)} price expression(s) in prose, but no Product/Offer structured data.",
                suggested_action="Add Schema.org Product markup with price, currency, and availability to ensure exact machine extraction."))

    # 3. Third-party Authority Links (sameAs)
    if not org["same_as"]:
        recommendations.append(dict(
            title="Declare authoritative sameAs profiles in Organization markup",
            category="entity-authority",
            rationale="No sameAs links to external authorities (Wikidata, Crunchbase, official social) were found in Organization schema.",
            suggested_action="Include sameAs URLs in Organization JSON-LD linking to verified third-party entities."))

    # 4. Answerability Coverage across sampled pages
    answerability_results = {}
    sampled_pages = [{"url": base + "/", "page_type": "homepage", "html": html}] + inv_pages

    for p in sampled_pages:
        ptype = p.get("page_type")
        if not ptype or ptype in ("homepage", "other"):
            continue
        p_dom = EntityDOMParser()
        try:
            p_dom.feed(p.get("html", ""))
        except Exception:
            continue
        p_text = " ".join(p_dom.text)
        ans = evaluate_page_answerability(ptype, p_text, p_dom, base)
        if ans:
            answerability_results[p["url"]] = ans
            observations.append(dict(
                id=f"OBS-{len(observations) + 1:03d}",
                category="answerability",
                source={"url": p["url"], "method": "page-type-analyzer"},
                observation=f"{ptype.title()} page answerability coverage: {ans['coverage_ratio']:.0%}",
                evidence=f"Present: {', '.join(ans['present']) or 'none'}; Missing: {', '.join(ans['missing']) or 'none'}",
                confidence="medium"
            ))
            if ans["coverage_ratio"] < 0.5:
                recommendations.append(dict(
                    title=f"Improve factual answerability on {ptype} page ({p['url']})",
                    category="answerability",
                    rationale=f"Material attributes ({', '.join(ans['missing'])}) are missing from this {ptype} page, reducing AI query answerability.",
                    suggested_action=f"Add clear, explicit text and markup for: {', '.join(ans['missing'])}."))

    overall_answerability = 1.0
    if answerability_results:
        overall_answerability = round(sum(a["coverage_ratio"] for a in answerability_results.values()) / len(answerability_results), 2)

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "entity_snapshot": {
            "organization": org,
            "products_count": len(products),
            "services_count": len(services),
            "word_count": words,
        },
        "coverage": {
            "pages_analyzed": len(sampled_pages),
            "answerability_index": overall_answerability,
            "answerability_by_page": answerability_results,
            "source": "shared-inventory" if inv is not None else "homepage-only"
        },
        "limitations": (["Answerability evaluated on raw HTML response text; client-rendered dynamic content not evaluated"] if inv_pages else [])
    }


def main():
    ap = argparse.ArgumentParser(description="Entity & content understanding audit layer.")
    ap.add_argument("--site", required=True)
    ap.add_argument("--inventory", help="Path to shared site-inventory JSON")
    args = ap.parse_args()
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
    print(json.dumps(audit(base, p.netloc, inv=inv), indent=2))


if __name__ == "__main__":
    main()
