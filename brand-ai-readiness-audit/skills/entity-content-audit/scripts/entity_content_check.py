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


def audit(base, domain):
    """Entity & content understanding audit.

    Contract: only measured understanding gaps become findings. Structured
    data absence is at most a recommendation. Inconclusive fetches surface
    status instead of a clean bill of health.
    """
    findings, recommendations = [], []

    status, html, _ = fetch(base + "/")
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

    return {"status": "ok", "findings": findings, "recommendations": recommendations,
            "entity": org, "products_found": len(products), "words": words}


def main():
    ap = argparse.ArgumentParser(description="Entity & content understanding audit layer.")
    ap.add_argument("--site", required=True)
    args = ap.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    print(json.dumps(audit(f"{p.scheme}://{p.netloc}", p.netloc), indent=2))


if __name__ == "__main__":
    main()
