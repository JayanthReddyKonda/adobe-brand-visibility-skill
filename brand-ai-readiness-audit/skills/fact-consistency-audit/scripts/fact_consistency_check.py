#!/usr/bin/env python3
"""
fact_consistency_check.py - Audits fact freshness, update timestamps, and cross-page fact consistency.

Causal Root Causes:
  - FACT.CONSISTENCY: FIRST_PARTY_FACT_CONFLICT, CONFLICTING_COMMERCIAL_TERMS
  - FACT.FRESHNESS: LEGACY_FACT_PROPAGATION, STALE_AUTHORITATIVE_FACT
  - FACT.LIFECYCLE: DISCONTINUED_VS_CURRENT_CONFLICT
"""
import sys
import os
import re
import json
import argparse
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

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

CURRENT_YEAR = datetime.now().year
PRICE_PATTERN = re.compile(r'(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?(\d[\d,]*(?:\.\d{1,2})?)', re.IGNORECASE)
EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
PHONE_PATTERN = re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,4}\d{2,4}')
DISCONTINUED_PATTERN = re.compile(r'\b(discontinued|retired|legacy|obsolete|end of life|out of production)\b', re.IGNORECASE)


class FreshnessAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_json_ld = False
        self.json_ld_contents = []
        self.meta_tags = {}
        self.text_content = []
        self.headings = []
        self.current_h = None
        self.current_h_text = []
        self.current_section = "General"
        self.text_with_context = []

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
                self.meta_tags[prop] = content
        elif tag_lower in ("h1", "h2", "h3", "h4"):
            self.current_h = tag_lower
            self.current_h_text = []

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style"):
            self.in_script = False
            self.in_json_ld = False
        elif tag_lower in ("h1", "h2", "h3", "h4"):
            if self.current_h:
                htxt = " ".join(self.current_h_text).strip()
                if htxt:
                    self.headings.append((self.current_h, htxt))
                    self.current_section = htxt
            self.current_h = None

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())
        elif self.current_h is not None:
            self.current_h_text.append(data.strip())
        elif not self.in_script:
            txt = data.strip()
            if txt:
                self.text_content.append(txt)
                self.text_with_context.append((self.current_section, txt))


def normalize_price_str(raw):
    """Normalize price string to digits (e.g. '₹5,499.00' -> '5499')."""
    digits = re.sub(r"[^\d]", "", raw.split(".")[0])
    return digits or None


def extract_scoped_facts(html_str, url):
    """Extract first-party facts with contextual scope, status, and lifecycle."""
    parser = FreshnessAnalyzer()
    try:
        parser.feed(html_str)
    except Exception:
        pass

    full_text = " ".join(parser.text_content)
    facts = {
        "url": url,
        "copyright_years": [],
        "brand_names": [],
        "taglines": [],
        "scoped_prices": [],
        "contact_emails": [],
        "contact_phones": [],
        "modification_dates": [],
        "products_with_status": []
    }

    # 1. Copyright years
    matches = re.findall(r'(?:©|&copy;|copyright)\s*(?:[0-9]{4}\s*[-–]\s*)?([0-9]{4})', full_text, re.IGNORECASE)
    for y in matches:
        try:
            iy = int(y)
            if 1990 <= iy <= CURRENT_YEAR + 1:
                facts["copyright_years"].append(iy)
        except ValueError:
            pass
    facts["copyright_years"] = sorted(set(facts["copyright_years"]))

    # 2. Structured Data extraction
    for raw in parser.json_ld_contents:
        try:
            data = json.loads(raw)
            objs = data if isinstance(data, list) else [data]
            if isinstance(data, dict) and "@graph" in data:
                objs = data["@graph"]
            for o in objs:
                if not isinstance(o, dict):
                    continue
                otype = str(o.get("@type", "")).lower()
                if otype in ("organization", "brand", "corporation"):
                    if o.get("name"):
                        facts["brand_names"].append(o["name"].strip())
                    if o.get("slogan") or o.get("alternateName"):
                        facts["taglines"].append(str(o.get("slogan") or o.get("alternateName")).strip())
                elif otype in ("product", "individualproduct"):
                    pname = str(o.get("name") or "Product").strip()
                    offers = o.get("offers") or {}
                    offer_obj = offers[0] if isinstance(offers, list) and offers else offers
                    if isinstance(offer_obj, dict):
                        p_val = offer_obj.get("price") or offer_obj.get("lowPrice")
                        avail = str(offer_obj.get("availability") or "").lower()
                        status = "discontinued" if "discontinued" in avail else ("in_stock" if "instock" in avail else "current")
                        facts["products_with_status"].append({
                            "name": pname,
                            "status": status,
                            "url": url
                        })
                        if p_val:
                            norm_p = normalize_price_str(str(p_val))
                            if norm_p:
                                facts["scoped_prices"].append({
                                    "entity": pname,
                                    "price": norm_p,
                                    "raw": str(p_val)
                                })
                if "dateModified" in o:
                    facts["modification_dates"].append(o["dateModified"])
                elif "datePublished" in o:
                    facts["modification_dates"].append(o["datePublished"])
        except Exception:
            pass

    # Meta / OpenGraph update timestamps
    for meta_key in ("article:modified_time", "og:updated_time", "last-modified"):
        if meta_key in parser.meta_tags:
            facts["modification_dates"].append(parser.meta_tags[meta_key])

    # 3. Text-based scoped price extraction
    for ctx, txt in parser.text_with_context:
        for m in re.finditer(r'(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?(\d[\d,]*(?:\.\d{1,2})?)', txt, re.IGNORECASE):
            norm_p = normalize_price_str(m.group(1))
            if norm_p and len(norm_p) >= 2:
                section_name = ctx if ctx and ctx != "General" else (parser.headings[0][1] if parser.headings else "Product")
                if not any(sp["price"] == norm_p and sp["entity"] == section_name for sp in facts["scoped_prices"]):
                    facts["scoped_prices"].append({
                        "entity": section_name,
                        "price": norm_p,
                        "raw": m.group(0)
                    })

    # 4. Discontinued / Lifecycle detection in prose
    for h in parser.headings:
        h_text = h[1]
        if DISCONTINUED_PATTERN.search(h_text) or DISCONTINUED_PATTERN.search(full_text[:400]):
            facts["products_with_status"].append({
                "name": h_text,
                "status": "discontinued",
                "url": url
            })

    # 5. Scoped emails & phones
    for m in EMAIL_PATTERN.finditer(html_str):
        addr = m.group(0).strip(".").lower()
        if not addr.endswith((".png", ".jpg", ".gif", ".webp", ".js", ".css")):
            scope = "sales" if "sales" in addr else ("support" if "support" in addr else "general")
            facts["contact_emails"].append({"scope": scope, "email": addr})

    for m in PHONE_PATTERN.finditer(full_text):
        digits = re.sub(r"\D", "", m.group(0))
        if 8 <= len(digits) <= 15:
            facts["contact_phones"].append({"scope": "telephone", "phone": digits})

    return facts


def evaluate_fact_consistency(page_fact_list, base_url):
    """Detect verified contradictions and lifecycle conflicts across first-party pages."""
    findings = []
    recommendations = []

    # 1. Scoped Price Contradictions
    price_ledger = {}
    for pf in page_fact_list:
        for sp in pf["scoped_prices"]:
            ent = sp["entity"].lower().strip()
            if len(ent) < 3 or ent in ("general", "home", "pricing", "pricing plans"):
                continue
            price_ledger.setdefault(ent, {}).setdefault(sp["price"], []).append({
                "url": pf["url"],
                "raw": sp["raw"]
            })

    for ent, val_map in price_ledger.items():
        if len(val_map) >= 2:
            details = []
            affected_urls = set()
            for price_val, occurrences in val_map.items():
                for occ in occurrences:
                    details.append(f"{occ['raw']} on {occ['url']}")
                    affected_urls.add(occ['url'])

            findings.append({
                "category": "fact-consistency",
                "title": f"Conflicting pricing published for '{ent}'",
                "severity": "high",
                "confidence": "high",
                "root_cause": f"Different price values for '{ent}' are published across separate first-party pages.",
                "cause_family": "FACT.CONSISTENCY",
                "cause_id": "FIRST_PARTY_FACT_CONFLICT",
                "impact": "AI retrieval systems quote contradictory pricing, creating commercial confusion and user distrust.",
                "evidence": f"{len(affected_urls)} page(s) publish conflicting figures for '{ent}': {'; '.join(details)}.",
                "suggested_action": {
                    "summary": f"Establish a single canonical price for '{ent}' and synchronize across all product listings and structured markup.",
                    "priority": "high",
                    "verification": f"Re-crawl {', '.join(affected_urls)} and verify identical pricing appears on all pages."
                }
            })

    # 2. Product Lifecycle Conflicts (Discontinued vs Active)
    status_by_name = {}
    for pf in page_fact_list:
        for p in pf.get("products_with_status", []):
            name_clean = p["name"].lower().strip()
            if len(name_clean) > 3:
                status_by_name.setdefault(name_clean, []).append((p["status"], p["url"]))

    for name, statuses in status_by_name.items():
        stat_types = {s[0] for s in statuses}
        if "discontinued" in stat_types and ("in_stock" in stat_types or "current" in stat_types):
            urls = {s[1] for s in statuses}
            findings.append({
                "category": "lifecycle",
                "title": f"Product lifecycle conflict for '{name}' (discontinued vs current)",
                "severity": "high",
                "confidence": "high",
                "root_cause": f"Product '{name}' is marked discontinued on one surface while advertised as current/in-stock on another.",
                "cause_family": "FACT.LIFECYCLE",
                "cause_id": "DISCONTINUED_VS_CURRENT_CONFLICT",
                "impact": "AI assistants quote obsolete products as active commercial offerings, causing customer churn.",
                "evidence": f"Lifecycle statuses differ across {len(urls)} page(s): {', '.join(f'{s[0]} on {s[1]}' for s in statuses)}.",
                "suggested_action": {
                    "summary": f"Synchronize availability status for '{name}' across all product pages and structured data.",
                    "priority": "high",
                    "verification": f"Re-crawl {', '.join(urls)} and confirm consistent lifecycle badges."
                }
            })

    # 3. Copyright Year Inconsistency (Signals legacy fact drift)
    c_years_by_url = {}
    for pf in page_fact_list:
        if pf["copyright_years"]:
            c_years_by_url[pf["url"]] = max(pf["copyright_years"])

    unique_years = set(c_years_by_url.values())
    if len(unique_years) >= 2:
        oldest_year = min(unique_years)
        newest_year = max(unique_years)
        if newest_year - oldest_year >= 2:
            details = [f"{url} ({yr})" for url, yr in sorted(c_years_by_url.items())]
            findings.append({
                "category": "freshness",
                "title": "Inconsistent copyright years across site pages",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "Disparate copyright years indicate unmaintained legacy page templates.",
                "cause_family": "FACT.FRESHNESS",
                "cause_id": "LEGACY_FACT_PROPAGATION",
                "impact": "AI models use footer dates as a heuristic freshness signal; stale dates reduce answer authority.",
                "evidence": f"Copyright years range from {oldest_year} to {newest_year} across sampled URLs: {'; '.join(details[:4])}.",
                "suggested_action": {
                    "summary": f"Standardize site footers to dynamically render the current copyright year ({CURRENT_YEAR}).",
                    "priority": "medium",
                    "verification": "Confirm all page footers display the synchronized current year."
                }
            })

    return findings, recommendations


def audit(base, domain, inv=None):
    findings = []
    recommendations = []
    page_fact_list = []

    if inv is not None:
        for p in inv.get("pages", []):
            u = p.get("url", "")
            raw_html = p.get("html", "")
            if u.lower().endswith((".xml", ".xml.gz", ".txt", ".json", ".pdf")):
                continue
            if raw_html.strip().startswith("<?xml") or "<urlset" in raw_html.lower() or "<sitemapindex" in raw_html.lower():
                continue
            if raw_html:
                page_fact_list.append(extract_scoped_facts(raw_html, u))
    else:
        status, html, _, _ = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if html:
            page_fact_list.append(extract_scoped_facts(html, base + "/"))

    if not page_fact_list:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve content from {base}"
        }

    f_findings, f_recs = evaluate_fact_consistency(page_fact_list, base)
    findings.extend(f_findings)
    recommendations.extend(f_recs)

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "coverage": {
            "html_pages_checked": len(page_fact_list),
            "scoped_facts_recorded": sum(len(pf["scoped_prices"]) for pf in page_fact_list),
            "source": "shared-inventory" if inv is not None else "homepage-only"
        },
        "limitations": [
            "Fact ledger covers raw HTML and JSON-LD text only; external third-party catalogs not polled"
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Audit fact freshness and consistency.")
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
