#!/usr/bin/env python3
"""
entity_content_check.py - Entity & content understanding layer.

Builds an entity snapshot (organization identity, products/offers, claims)
from first-party pages and structured data, and evaluates whether a machine
could understand WHO this is and WHAT it offers. Structured-data absence is
never a defect by itself; only measured understanding gaps are reported,
with confidence reflecting the evidence level.
"""
import sys, os, re, json, argparse
import urllib.request, urllib.error
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

UA = {"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0)"}
PRICE_RE = re.compile(r'(?:₹|Rs\.?|\$|€|£)\s?\d[\d,]*(?:\.\d{1,2})?')


def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", {}
    except Exception:
        return None, "", {}


class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.skip, self.in_title = [], 0, False
        self.title, self.og = "", {}
        self.json_ld, self.h1, self.images_no_alt = [], [], 0
        self.images = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = tag.lower()
        if t in ("script", "style", "noscript"):
            self.skip += 1
        if t == "title":
            self.in_title = True
        if t == "meta":
            p, c = a.get("property", ""), a.get("content", "")
            if p.startswith("og:"):
                self.og[p] = c
        if t == "script" and "ld+json" in (a.get("type") or ""):
            self._ld = True
        if t == "img":
            self.images += 1
            if not a.get("alt"):
                self.images_no_alt += 1
        if t == "h1":
            self._h1 = True

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        if t == "title":
            self.in_title = False
        if t == "script":
            self._ld = False
        if t == "h1":
            self._h1 = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        if self._ld:
            self.json_ld.append(data)
        elif not self.skip and data.strip():
            self.text.append(data.strip())


def extract_entities(dom, base):
    org = {"name": dom.og.get("og:site_name") or dom.title.strip() or None,
           "logo": dom.og.get("og:image"), "same_as": [], "type": None}
    products, dates = [], []
    for raw in dom.json_ld:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for o in objs:
            if not isinstance(o, dict):
                continue
            t = str(o.get("@type", ""))
            if t.lower() in ("organization", "brand", "localbusiness", "store"):
                org["type"] = t
                org["name"] = o.get("name") or org["name"]
                org["logo"] = o.get("logo") or org["logo"]
                sa = o.get("sameAs") or []
                org["same_as"] += sa if isinstance(sa, list) else [sa]
            elif t.lower() in ("product",):
                offers = o.get("offers") or {}
                products.append(dict(
                    name=o.get("name"), description=o.get("description"),
                    price=(offers.get("price") or offers.get("lowPrice")) if isinstance(offers, dict) else None,
                    currency=(offers.get("priceCurrency") if isinstance(offers, dict) else None),
                    availability=(offers.get("availability") if isinstance(offers, dict) else None)))
            if "dateModified" in o or "datePublished" in o:
                dates.append(o.get("dateModified") or o.get("datePublished"))
    return org, products, dates


def audit(base, domain, inv=None):
    """Entity & content understanding audit.

    Contract: only measured understanding gaps become findings. Structured
    data absence is at most a recommendation. Inconclusive fetches surface
    status instead of a clean bill of health. When `inv` (shared site
    inventory from the orchestrator) is supplied, its pages are used as the
    evidence snapshot and page-type-aware attribute coverage is measured.
    """
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
        status, html = fetch(base + "/")[:2]
        inv_pages = []
    if status is None:
        return {"status": "inconclusive", "findings": [], "recommendations": [],
                "error": f"could not reach {base}"}

    dom = Dom()
    try:
        dom.feed(html)
    except Exception:
        pass

    org, products, dates = extract_entities(dom, base)
    words = len(" ".join(dom.text).split())
    content_bearing = words >= 50

    if not content_bearing:
        return {"status": "inconclusive", "findings": findings, "recommendations": recommendations,
                "error": f"initial HTML carries only {words} words; entity analysis needs rendered content "
                         f"(see discoverability-audit rendering findings)"}

    # 1. Identity explicitness: can a machine tell WHO this is?
    identity_signals = sum(x is not None for x in (org["name"], org["logo"], org["type"]))
    if identity_signals == 0:
        findings.append(dict(
            category="entity-integrity", title="Organization identity not machine-explicit",
            severity="medium", confidence="medium",
            root_cause="No Organization/Brand structured data, no og:site_name, and no extractable <title> identity.",
            impact="AI systems must infer the brand name from surrounding prose; disambiguation against similarly named entities is unreliable.",
            evidence=f"{base}/ carries {words} words but yields no explicit organization name, logo, or type from metadata or JSON-LD.",
            suggested_action=dict(
                summary="Declare identity explicitly: Organization JSON-LD (name, logo, url, sameAs) plus og:site_name.",
                priority="medium",
                verification="Re-fetch and confirm Organization JSON-LD parses with name and logo present.")))

    # 2. Offer/product explicitness: can a machine tell WHAT is offered?
    if not products:
        # Look for price-like text as a weak signal of an offer buried in prose
        price_hits = PRICE_RE.findall(" ".join(dom.text))
        rec = dict(
            title="Make product/offer facts machine-extractable",
            rationale=f"No Product structured data found. {len(price_hits)} price-like string(s) exist in prose"
                      + (" - facts are present but not extractable as structured offers." if price_hits else
                         "; neither structured nor clearly stated offers were found."),
            suggested_action="Add Product JSON-LD (name, description, offers.price, availability) for flagship offerings.")
        recommendations.append(rec)

    # 3. Claim completeness: flagship entity attribute coverage (L2/L3)
    if products:
        for p in products:
            missing = [k for k in ("price", "description", "availability") if not p.get(k)]
            if missing:
                findings.append(dict(
                    category="content-quality",
                    title=f"Product '{p.get('name')}' lacks explicit attributes",
                    severity="low", confidence="high",
                    root_cause="Structured Product data exists but omits material attributes.",
                    impact="Incomplete offers cannot be quoted confidently; AI may omit the product or fill gaps by inference.",
                    evidence=f"Product JSON-LD on {base}/ is missing: {', '.join(missing)}.",
                    suggested_action=dict(
                        summary=f"Add the missing fields ({', '.join(missing)}) to the Product markup.",
                        priority="low",
                        verification="Re-parse JSON-LD and confirm all fields resolve.")))

    # 4. sameAs corroboration hook (deferred detail to corroboration layer)
    if not org["same_as"]:
        recommendations.append(dict(
            title="Add sameAs links to the Organization entity",
            rationale="No sameAs links were found. Without them, AI systems cannot tie this site to Wikidata/social/registry identities. Absence alone is not ambiguity - add them to preempt disambiguation risk.",
            suggested_action="List authoritative profile URLs (Wikidata, registries, official social) in Organization.sameAs."))

    # 5. Page-type-aware attribute coverage (answerability layer): for each
    #    inventory page of a known type, measure whether the expected material
    #    attributes are present. Gaps become RECOMMENDATIONS with a measured
    #    coverage ratio — not defects (absence of an attribute is not proof of
    #    a defect; it is an answerability gap).
    EXPECTED_ATTRS = {
        "product": ["name", "price", "description", "availability", "brand"],
        "pricing": ["price", "plan", "currency-or-unit"],
        "location": ["address", "hours", "phone"],
        "documentation": ["version", "example", "command-or-api"],
        "contact": ["email-or-form", "phone", "address"],
    }
    attr_coverage = {}
    for page in inv_pages:
        ptype = page.get("page_type")
        expected = EXPECTED_ATTRS.get(ptype)
        if not expected:
            continue
        pd = Dom()
        try:
            pd.feed(page["html"])
        except Exception:
            continue
        text = " ".join(pd.text).lower()
        porg, pprods, _ = extract_entities(pd, base)
        present = []
        if ptype == "product":
            if pd.title: present.append("name")
            if pprods and any(p.get("price") for p in pprods): present.append("price")
            if pprods and any(p.get("description") for p in pprods): present.append("description")
            if pprods and any(p.get("availability") for p in pprods): present.append("availability")
            if pprods and any(p.get("name") for p in pprods): present.append("brand")
        else:
            markers = {"pricing": {"price": PRICE_RE.search(text), "plan": "plan" in text,
                                   "currency-or-unit": bool(PRICE_RE.search(text))},
                       "location": {"address": "address" in text, "hours": "hours" in text or "open" in text,
                                    "phone": bool(re.search(r"\+?\d[\d\s().-]{7,}\d", text))},
                       "documentation": {"version": "version" in text or "v[0-9]" in text,
                                         "example": "example" in text,
                                         "command-or-api": "api" in text or "$ " in text or "npm" in text},
                       "contact": {"email-or-form": "@" in text or "form" in text,
                                   "phone": bool(re.search(r"\+?\d[\d\s().-]{7,}\d", text)),
                                   "address": "address" in text}}
            present = [k for k, hit in markers.get(ptype, {}).items() if hit]
        ratio = round(len(set(present)) / len(expected), 2) if expected else 1.0
        attr_coverage[page["url"]] = {"page_type": ptype, "present": sorted(set(present)),
                                      "missing": sorted(set(expected) - set(present)),
                                      "coverage": ratio}
        observations.append(dict(
            id=f"OBS-{len(observations) + 1:03d}", category="answerability",
            source={"url": page["url"], "method": "shared-inventory"},
            observation=f"{ptype} page attribute coverage {ratio:.0%}",
            evidence=f"present: {', '.join(sorted(set(present))) or 'none'}; missing: {', '.join(sorted(set(expected) - set(present))) or 'none'}",
            confidence="medium"))
        if ratio < 0.6:
            recommendations.append(dict(
                title=f"Add missing material attributes to {ptype} page ({page['url']})",
                rationale=f"Measured attribute coverage is {ratio:.0%}. Missing material facts reduce answerability: "
                          "questions a user would ask about this page cannot be answered from its content.",
                suggested_action=f"State the missing attributes explicitly: {', '.join(sorted(set(expected) - set(present)))}."))

    return {"status": "ok", "findings": findings, "recommendations": recommendations,
            "entity": org, "products_found": len(products), "words": words,
            "observations": observations,
            "coverage": {"pages_analyzed": 1 + len(inv_pages), "attribute_coverage": attr_coverage,
                         "source": "shared-inventory" if inv is not None else "homepage-only"},
            "limitations": (["attribute coverage measured against keyword/JSON-LD markers only; "
                             "rendered or image-borne attributes are not visible in raw HTML"] if inv_pages else [])}


def main():
    ap = argparse.ArgumentParser(description="Entity & content understanding audit layer.")
    ap.add_argument("--site", required=True)
    ap.add_argument("--inventory", help="Path to shared site-inventory JSON (from audit-orchestrator)")
    args = ap.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    print(json.dumps(audit(f"{p.scheme}://{p.netloc}", p.netloc, inv=inv), indent=2))


if __name__ == "__main__":
    main()
