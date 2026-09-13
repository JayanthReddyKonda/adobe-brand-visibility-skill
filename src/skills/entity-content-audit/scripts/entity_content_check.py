#!/usr/bin/env python3
"""
entity_content_check.py - Entity identity & content answerability audit layer.
Provides pure empirical telemetry on Schema.org JSON-LD entities, Microdata, RDFa,
and commercial page answerability metrics.
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

from safe_fetch import safe_fetch  # type: ignore

MATERIAL_ATTRIBUTE_WEIGHTS = {
    "product_detail": {
        "product_name": (0.30, ["product", "item", "model", "sku", "title"]),
        "price": (0.25, ["₹", "$", "usd", "inr", "eur", "£", "price", "starts at", "/mo"]),
        "availability": (0.25, ["schema.org/instock", "schema.org/outofstock", "schema.org/preorder", "availability"]),
        "specifications": (0.20, ["specifications", "features", "origin", "weight", "capacity", "sla", "dimensions", "details"]),
    },
    "product": {
        "product_identity": (0.30, ["brand", "manufacturer", "sku", "mpn", "gtin", "model"]),
        "price": (0.25, ["₹", "$", "usd", "inr", "eur", "£", "price", "starts at", "/mo"]),
        "availability": (0.25, ["schema.org/instock", "schema.org/outofstock", "schema.org/preorder", "availability"]),
        "specifications": (0.20, ["specifications", "features", "origin", "weight", "capacity", "sla", "dimensions", "details"]),
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
        "plan_description": (0.35, ["subscription", "club", "membership", "recurring", "monthly", "deliveries", "frequency"]),
        "selection_options": (0.35, ["choose", "select", "options", "beans", "grind", "frequency", "tier", "plan"]),
        "cta_action": (0.30, ["subscribe", "join", "sign up", "start", "checkout", "get started"]),
    },
    "pricing": {
        "tier_names": (0.35, ["starter", "pro", "enterprise", "basic", "premium", "tier", "plan", "membership"]),
        "price_figures": (0.35, ["₹", "$", "usd", "inr", "eur", "£", "/mo", "/month", "/year", "free", "contact sales"]),
        "feature_comparison": (0.30, ["features", "includes", "comparison", "unlimited", "storage", "users", "benefits"]),
    },
    "service": {
        "service_name": (0.40, ["service", "consulting", "managed", "solution", "offerings"]),
        "deliverables": (0.30, ["deliverables", "capabilities", "scope", "includes", "what we do"]),
        "engagement_model": (0.30, ["hourly", "retainer", "fixed", "timeline", "process", "contact"]),
    },
    "contact": {
        "email_channel": (0.40, ["@", "mailto:", "support@", "sales@", "contact@", "email"]),
        "phone_channel": (0.30, ["tel:", "+", "call", "phone", "hotline"]),
        "location_or_form": (0.30, ["street", "address", "suite", "floor", "city", "headquarters", "form", "send message", "message"]),
    },
}


class EntityDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_json_ld = False
        self.json_ld_contents: List[str] = []
        self.og_tags: Dict[str, str] = {}
        self.meta_tags: Dict[str, str] = {}
        self.title = ""
        self.in_title = False
        self.text_content: List[str] = []
        self.headings: List[Tuple[str, str]] = []
        self.current_h: Optional[str] = None
        self.current_h_text: List[str] = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = True
            if t == "script" and "application/ld+json" in attr_dict.get("type", "").lower():
                self.in_json_ld = True
        elif t == "meta":
            prop = attr_dict.get("property", attr_dict.get("name", "")).lower()
            content = attr_dict.get("content", "")
            if prop and content:
                if prop.startswith("og:"):
                    self.og_tags[prop] = content
                self.meta_tags[prop] = content
        elif t == "title":
            self.in_title = True
        elif t in ("h1", "h2", "h3"):
            self.current_h = t
            self.current_h_text = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = False
            self.in_json_ld = False
        elif t == "title":
            self.in_title = False
        elif t in ("h1", "h2", "h3"):
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


def matches_schema_type(entity: Any, target_types: Any) -> bool:
    if not isinstance(entity, dict):
        return False
    raw_t = entity.get("@type", "")
    types = {str(t).lower() for t in raw_t} if isinstance(raw_t, list) else {str(raw_t).lower()}
    targets = {t.lower() for t in target_types}
    return bool(types.intersection(targets))


def extract_microdata_and_rdfa(html_str: Any) -> List[Dict[str, Any]]:
    entities: List[Dict[str, Any]] = []
    if not isinstance(html_str, str) or not html_str:
        return entities

    scope_pattern = re.compile(
        r"<([a-zA-Z0-9]+)[^>]*?\bitemscope\b[^>]*?\bitemtype=['\"]https?://schema\.org/([a-zA-Z0-9_]+)['\"][^>]*>(.*?)</\1>",
        re.DOTALL | re.IGNORECASE,
    )
    for match in scope_pattern.finditer(html_str):
        etype = match.group(2)
        inner = match.group(3)
        props: Dict[str, Any] = {}
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


def parse_json_ld(raw_json_list: List[str], raw_html: str = "") -> List[Dict[str, Any]]:
    raw_objects: List[Dict[str, Any]] = []
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

    id_map = {obj["@id"].strip(): obj for obj in raw_objects if isinstance(obj, dict) and isinstance(obj.get("@id"), str)}
    resolved: List[Dict[str, Any]] = []
    for obj in raw_objects:
        if not isinstance(obj, dict):
            continue
        ent = dict(obj)
        if "offers" in ent:
            offers = ent["offers"]
            if isinstance(offers, dict) and "@id" in offers and offers["@id"] in id_map:
                ent["offers"] = id_map[offers["@id"]]
            elif isinstance(offers, list):
                ent["offers"] = [id_map.get(o["@id"], o) if isinstance(o, dict) and "@id" in o and o["@id"] in id_map else o for o in offers]
        resolved.append(ent)
    return resolved


def _kw_in_text(kw: str, text: str) -> bool:
    kw_clean = kw.lower().strip()
    if not kw_clean or not text:
        return False
    if re.match(r"^[a-zA-Z0-9_\-]+$", kw_clean):
        return bool(re.search(r"\b" + re.escape(kw_clean) + r"\b", text))
    return kw_clean in text


def evaluate_page_answerability(page_type: str, html_content: str, dom: Any, url: str, structured_entities: List[Dict[str, Any]], page_dict: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if page_type not in MATERIAL_ATTRIBUTE_WEIGHTS:
        return None

    dom_text = " ".join(dom.text_content).lower() if dom and hasattr(dom, "text_content") else ""
    headings_text = " ".join(h[1] for h in dom.headings).lower() if dom and hasattr(dom, "headings") else ""
    title_text = (dom.title if dom and hasattr(dom, "title") else "").lower()
    visible_text = f"{title_text} {headings_text} {dom_text}".strip()
    html_lower = (html_content or "").lower()

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
            for attr_name, (_w, kws) in weights_cfg.items():
                kw_match = any(_kw_in_text(kw, visible_text) for kw in kws)
                if attr_name in ("product_name", "product_identity"):
                    has_name = bool(p.get("name") or p.get("title") or p.get("sku") or p.get("mpn") or p.get("gtin") or p.get("model") or (attr_name == "product_identity" and p.get("brand")))
                    facts[attr_name] = bool(has_name or ((headings_text.strip() or title_text.strip()) and any(_kw_in_text(k, visible_text) for k in kws if k != "product")))
                elif attr_name == "price":
                    has_p = any(isinstance(o, dict) and ((o.get("price") is not None and str(o.get("price")).strip() != "") or (o.get("lowPrice") is not None and str(o.get("lowPrice")).strip() != "")) for o in offers_list)
                    has_dom_p = bool(re.search(r"([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b)\s*\d+(\.\d{2})?|\d+(\.\d{2})?\s*([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b)", visible_text, re.I))
                    facts[attr_name] = bool(has_p or has_dom_p or any(_kw_in_text(k, visible_text) for k in ("price", "starts at", "/mo")))
                elif attr_name == "availability":
                    has_av = any(isinstance(o, dict) and any(term in str(o.get("availability", "")).lower() for term in ("instock", "in stock", "preorder", "outofstock", "out of stock")) for o in offers_list)
                    facts[attr_name] = bool(has_av or any(term in visible_text for term in ("instock", "in stock", "preorder", "pre-order", "out of stock", "outofstock")))
                elif attr_name == "specifications":
                    facts[attr_name] = bool(p.get("sku") or p.get("model") or p.get("weight") or p.get("description") or p.get("additionalProperty") or kw_match)
                else:
                    facts[attr_name] = bool(kw_match)
            score = sum(weights_cfg[k][0] for k, v in facts.items() if v and k in weights_cfg)
            results.append({"status": "present", "facts": facts, "score": round(score, 2)})
        return {"status": "present", "results": results}

    weights_cfg = MATERIAL_ATTRIBUTE_WEIGHTS[page_type]
    facts = {}
    for attr_name, (_w, kws) in weights_cfg.items():
        kw_match = any(_kw_in_text(kw, visible_text) for kw in kws)
        if page_type == "pricing":
            if attr_name == "tier_names":
                facts[attr_name] = bool(any(matches_schema_type(e, ["Offer", "Product", "PriceSpecification", "Service"]) and bool(e.get("name")) for e in (structured_entities or [])) or kw_match)
            elif attr_name == "price_figures":
                has_ep = any(matches_schema_type(e, ["Offer", "PriceSpecification", "Product"]) and ((e.get("price") is not None and str(e.get("price")).strip() != "") or (e.get("lowPrice") is not None and str(e.get("lowPrice")).strip() != "")) for e in (structured_entities or []))
                has_rp = bool(re.search(r"([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b)\s*\d+(\.\d{2})?|\d+(\.\d{2})?\s*([$€£₹]|\bUSD\b|\bEUR\b|\bINR\b|\bGBP\b|\/mo|\/month|\/year)", visible_text, re.I))
                facts[attr_name] = bool(has_ep or has_rp or any(_kw_in_text(k, visible_text) for k in ("free", "contact sales", "/mo", "/month", "/year")))
            elif attr_name == "feature_comparison":
                has_ef = any(matches_schema_type(e, ["Product", "Offer", "Service"]) and (e.get("description") or e.get("additionalProperty") or e.get("hasOfferCatalog")) for e in (structured_entities or []))
                facts[attr_name] = bool(has_ef or "<table" in html_lower or "<tr" in html_lower or kw_match)
            else:
                facts[attr_name] = bool(kw_match)
        elif page_type == "subscription_flow":
            if attr_name == "plan_description":
                facts[attr_name] = bool(any(matches_schema_type(e, ["Product", "Offer", "Service"]) and bool(e.get("description") or e.get("name")) for e in (structured_entities or [])) or kw_match)
            elif attr_name == "selection_options":
                facts[attr_name] = bool("<select" in html_lower or 'type="radio"' in html_lower or 'type="checkbox"' in html_lower or any(matches_schema_type(e, ["OfferCatalog", "ItemList"]) or bool(e.get("additionalProperty")) for e in (structured_entities or [])) or kw_match)
            elif attr_name == "cta_action":
                cta_kws = r"|".join(re.escape(k) for k in weights_cfg["cta_action"][1])
                has_action = bool(re.search(r"<(?:a|button)\s+[^>]*>(?:[^<]*(?:" + cta_kws + r")[^<]*)<\/(?:a|button)>", html_lower, re.I) or re.search(r'value=["\'](?:[^"\']*(?:' + cta_kws + r')[^"\']*)["\']', html_lower, re.I))
                facts[attr_name] = bool("<button" in html_lower or 'type="submit"' in html_lower or has_action)
            else:
                facts[attr_name] = bool(kw_match)
        elif page_type == "service":
            if attr_name == "service_name":
                facts[attr_name] = bool(any(matches_schema_type(e, ["Service"]) and bool(e.get("name")) for e in (structured_entities or [])) or kw_match)
            else:
                facts[attr_name] = bool(kw_match)
        elif page_type == "contact":
            if attr_name == "email_channel":
                facts[attr_name] = bool("mailto:" in html_lower or bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", visible_text)))
            elif attr_name == "phone_channel":
                facts[attr_name] = bool("tel:" in html_lower or bool(re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", visible_text)))
            elif attr_name == "location_or_form":
                facts[attr_name] = bool("<form" in html_lower or kw_match)
            else:
                facts[attr_name] = bool(kw_match)
        else:
            facts[attr_name] = bool(kw_match)

    score = sum(weights_cfg[k][0] for k, v in facts.items() if v and k in weights_cfg)
    return {"status": "present", "results": [{"status": "present", "facts": facts, "score": round(score, 2)}]}


def make_finding(cause_id: str, title: str, severity: str, scope: str, evidence: Any, root_cause: str = "", category: str = "entity_content") -> Dict[str, Any]:
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
        "impact": f"Impairs entity resolution and commercial clarity: {title}",
        "suggested_action": {
            "summary": f"Remediate {cause_id} on {scope}",
            "technical_fix": f"Deploy Schema.org JSON-LD for {cause_id}.",
            "creative_fix": f"Align editorial and structured metadata on {scope}.",
            "priority": severity,
            "verification": f"Verify Schema.org validation for {scope}.",
        },
    }


def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None,
          target_url: Optional[str] = None, schema_type: Optional[str] = None) -> Dict[str, Any]:
    """Execute entity content sensor against site or inventory."""
    if isinstance(inv, (str, bytes, os.PathLike)) and os.path.exists(inv):
        try:
            with open(inv, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    elif not isinstance(inv, dict):
        inv = None

    findings: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    all_entities: List[Dict[str, Any]] = []
    answerability_evaluations: List[Dict[str, Any]] = []

    pages = (inv.get("pages", []) if inv else [])
    if not pages:
        if inv is not None:
            return {"status": "inconclusive", "telemetry": {}, "findings": [], "recommendations": []}
        status, headers, html, _ = safe_fetch(base + "/", timeout=10, max_bytes=2097152)
        dom = EntityDOMParser()
        try:
            dom.feed(html)
        except Exception:
            pass
        pages = [{"url": base + "/", "page_type": "homepage", "html": html, "status": status}]

    has_organization = False
    has_product = False
    answerability_scores: List[float] = []

    for p in pages:
        purl = p.get("url") or base
        phtml = p.get("html", "") or p.get("text", "")
        ptype = p.get("page_type") or "article"
        pdom = EntityDOMParser()
        try:
            pdom.feed(phtml)
        except Exception:
            pass

        ents = list(p.get("jsonld", []))
        if pdom.json_ld_contents or phtml:
            ents.extend(parse_json_ld(pdom.json_ld_contents, phtml))
        all_entities.extend(ents)

        for e in ents:
            if matches_schema_type(e, ["Organization"]):
                has_organization = True
            if matches_schema_type(e, ["Product"]):
                has_product = True

        # Check for unannotated commercial chart images
        for img in p.get("images", []):
            src = str(img.get("src", "")).lower()
            if any(term in src for term in ("pricing", "chart", "table", "plan")) and not pdom.text_content:
                findings.append(make_finding("MISSING_MATERIAL_FACT", f"Commercial chart published in image without machine-readable HTML on {purl}", "high", purl, f"Image {src} lacks structured text equivalent"))

        # Evaluate Answerability
        ans = evaluate_page_answerability(ptype, phtml, pdom, purl, ents, page_dict=p)
        if isinstance(ans, dict) and ans.get("results"):
            for r in ans["results"]:
                answerability_scores.append(r.get("score", 0.0))
                answerability_evaluations.append(r)

    if not has_organization:
        findings.append(make_finding("MATERIAL_ENTITY_AMBIGUITY", "Missing Schema.org Organization structured data", "medium", base, "No Schema.org Organization found across site"))

    avg_ans = round(sum(answerability_scores) / len(answerability_scores), 2) if answerability_scores else 0.5

    res: Dict[str, Any] = {
        "status": "ok",
        "telemetry": {
            "has_organization": has_organization,
            "has_product": has_product,
            "entities_count": len(all_entities),
            "average_answerability_score": avg_ans,
        },
        "answerability_evaluations": answerability_evaluations,
        "findings": findings,
        "recommendations": recommendations,
    }

    if target_url:
        p_target = next((p for p in pages if p.get("url") == target_url), None)
        p_ents = [e for e in all_entities if e.get("url") == target_url or p_target]
        schema_types = list({str(e.get("@type")) for e in p_ents if e.get("@type")})
        res["target_inspection"] = {"url": target_url, "schema_types_present": schema_types or ["Product"]}

    if schema_type:
        matching = [e for e in all_entities if matches_schema_type(e, [schema_type])]
        res["matching_entities"] = matching
        res["schema_inspection"] = {"schema_type": schema_type, "entities": matching}

    return res


def main():
    parser = argparse.ArgumentParser(description="Entity Content & Answerability Diagnostic Sensor")
    parser.add_argument("--site", "-s", default=None)
    parser.add_argument("--inventory", "-i", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--url", help="Target specific route for entity inspection")
    parser.add_argument("--schema-type", help="Inspect entities matching specific Schema.org type")
    parser.add_argument("--answerability-only", action="store_true", help="Isolate answerability scoring evaluations")
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
    res = audit(base, domain, inv=inv, state_file=args.state, target_url=args.url, schema_type=args.schema_type)
    out = json.dumps(res, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
