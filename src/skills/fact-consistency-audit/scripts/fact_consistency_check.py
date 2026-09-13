#!/usr/bin/env python3
"""
fact_consistency_check.py - Audits cross-page fact consistency, prices, and freshness.
Constructs a multi-attribute first-party fact ledger to isolate verified contradictions.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore

CURRENT_YEAR = datetime.now(timezone.utc).year
PRICE_PATTERN = re.compile(r"(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?(\d[\d,]*(?:\.\d{1,2})?)", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,4}\d{2,4}")


def extract_currency(raw_str: Optional[str]) -> str:
    raw = raw_str or ""
    s = raw.upper()
    if "₹" in raw or "INR" in s or "RS" in s:
        return "INR"
    if "R$" in s or "BRL" in s:
        return "BRL"
    if "C$" in s or "CAD" in s:
        return "CAD"
    if "A$" in s or "AUD" in s:
        return "AUD"
    if "$" in raw or "USD" in s:
        return "USD"
    if "€" in raw or "EUR" in s:
        return "EUR"
    if "£" in raw or "GBP" in s:
        return "GBP"
    if "¥" in raw or "JPY" in s or "CNY" in s or "RMB" in s:
        return "JPY"
    if "AED" in s or "DHS" in s:
        return "AED"
    return "UNKNOWN"


def extract_interval(raw_str: Optional[str]) -> str:
    s = (raw_str or "").lower()
    if re.search(r"(\bmonthly\b|\bper\s+month\b|/\s*mo\b|/\s*month\b|\bper\s+user/mo\b|\bper\s+seat/mo\b|/\s*user/month\b|/\s*seat/month\b|\bbilled\s+monthly\b)", s):
        return "month"
    if re.search(r"(\bannually\b|\bannual\b|\byearly\b|\bper\s+year\b|/\s*yr\b|/\s*year\b|\bbilled\s+annually\b|\bbilled\s+yearly\b|/\s*user/year\b|/\s*seat/year\b)", s):
        return "year"
    if re.search(r"(\bweekly\b|\bper\s+week\b|/\s*wk\b|/\s*week\b)", s):
        return "week"
    if re.search(r"(\bdaily\b|\bper\s+day\b|/\s*day\b)", s):
        return "day"
    return "one_time"


def normalize_price_str(raw: Any, currency: Optional[str] = None) -> Optional[str]:
    if not raw:
        return None
    s = str(raw).strip()
    if re.search(r"\d+\.\d{3},\d{2}", s):
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        s = (parts[0] + "." + parts[1]) if len(parts) == 2 and len(parts[1]) == 2 else s.replace(",", "")

    m = re.search(r"(\d+(?:\.\d{1,2})?)", s)
    if not m:
        return None
    try:
        val = float(m.group(1))
        return f"{val:.2f}"
    except ValueError:
        return None


class FreshnessAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_json_ld = False
        self.json_ld_contents: List[str] = []
        self.meta_tags: Dict[str, str] = {}
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
                self.meta_tags[prop] = content
        elif t in ("h1", "h2", "h3", "h4"):
            self.current_h = t
            self.current_h_text = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = False
            self.in_json_ld = False
        elif t in ("h1", "h2", "h3", "h4"):
            if self.current_h and self.current_h_text:
                self.headings.append((self.current_h, " ".join(self.current_h_text).strip()))
            self.current_h = None

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())
        elif self.current_h is not None:
            self.current_h_text.append(data.strip())
        elif not self.in_script and data.strip():
            self.text_content.append(data.strip())


def extract_scoped_facts(html: str, url: str) -> Dict[str, Any]:
    """Extract structured facts (prices, currency, billing interval) from HTML JSON-LD."""
    parser = FreshnessAnalyzer()
    try:
        parser.feed(html)
    except Exception:
        pass
    scoped_prices: List[Dict[str, Any]] = []
    for jstr in parser.json_ld_contents:
        try:
            data = json.loads(jstr)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    offers = item.get("offers", item)
                    off_list = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []
                    for off in off_list:
                        if isinstance(off, dict):
                            p = normalize_price_str(off.get("price"))
                            cur = off.get("priceCurrency") or extract_currency(str(off.get("price")))
                            pspec = off.get("priceSpecification")
                            unit = ""
                            if isinstance(pspec, dict):
                                unit = str(pspec.get("unitCode", "")).upper()
                                if not p and pspec.get("price"):
                                    p = normalize_price_str(pspec.get("price"))
                            if not unit:
                                unit = str(off.get("unitCode", "")).upper()
                            interval = "month" if unit in ("MON", "MONTH") else extract_interval(str(pspec or ""))
                            if p:
                                scoped_prices.append({"price": p, "currency": cur, "interval": interval, "url": url})
        except Exception:
            pass
    return {"scoped_prices": scoped_prices, "url": url}


def make_finding(cause_id: str, title: str, severity: str, scope: str, evidence: Any, root_cause: str = "", category: str = "fact_consistency") -> Dict[str, Any]:
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
        "impact": f"Triggers LLM hallucination or conflicting citations: {title}",
        "suggested_action": {
            "summary": f"Remediate {cause_id} on {scope}",
            "technical_fix": f"Synchronize data sources for {cause_id}.",
            "creative_fix": f"Ensure consistent factual claims across {scope}.",
            "priority": severity,
            "verification": f"Verify consistency on {scope}.",
        },
    }


def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None,
          attribute: Optional[str] = None, compare_urls: Optional[List[str]] = None, query: Optional[str] = None) -> Dict[str, Any]:
    """Execute fact consistency sensor against site or inventory."""
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

    pages = inv.get("pages", []) if inv else []
    if not pages:
        if inv is not None:
            return {"status": "inconclusive", "telemetry": {}, "findings": [], "recommendations": []}
        st, _, html, _ = safe_fetch(base + "/", timeout=10, max_bytes=2097152)
        pages = [{"url": base + "/", "page_type": "homepage", "html": html, "status": st}]

    # Build first-party fact ledger
    fact_ledger: List[Dict[str, Any]] = []
    prices_by_page: Dict[str, List[Dict[str, Any]]] = {}

    for p in pages:
        purl = p.get("url") or base
        phtml = p.get("html", "") or p.get("text", "")
        pdom = FreshnessAnalyzer()
        try:
            pdom.feed(phtml)
        except Exception:
            pass

        # 1. Prices from JSON-LD
        jsonld_blocks = list(p.get("jsonld", []))
        for jstr in pdom.json_ld_contents:
            try:
                parsed = json.loads(jstr)
                if isinstance(parsed, list):
                    jsonld_blocks.extend(parsed)
                elif isinstance(parsed, dict):
                    if "@graph" in parsed and isinstance(parsed["@graph"], list):
                        jsonld_blocks.extend(parsed["@graph"])
                    else:
                        jsonld_blocks.append(parsed)
            except Exception:
                pass

        page_prices: List[Dict[str, Any]] = []
        for obj in jsonld_blocks:
            if not isinstance(obj, dict):
                continue
            t = str(obj.get("@type", "")).lower()
            if "offer" in t or "product" in t:
                offers = obj.get("offers", obj)
                off_list = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []
                for off in off_list:
                    if isinstance(off, dict):
                        p_val = normalize_price_str(off.get("price"))
                        cur = off.get("priceCurrency") or extract_currency(str(off.get("price")))
                        unit = str(off.get("unitCode", "")).upper()
                        interval = "month" if unit in ("MON", "MONTH") else extract_interval(str(off.get("priceSpecification", "")))
                        if p_val:
                            entry = {"url": purl, "price": p_val, "currency": cur, "interval": interval, "source": "schema"}
                            page_prices.append(entry)
                            fact_ledger.append(entry)

        # 2. Prices from text
        all_text = " ".join(pdom.text_content)
        for m in PRICE_PATTERN.finditer(all_text):
            p_val = normalize_price_str(m.group(0))
            cur = extract_currency(m.group(0))
            surrounding = all_text[max(0, m.start() - 30):min(len(all_text), m.end() + 30)]
            interval = extract_interval(surrounding)
            if p_val:
                entry = {"url": purl, "price": p_val, "currency": cur, "interval": interval, "source": "text"}
                page_prices.append(entry)
                fact_ledger.append(entry)

        prices_by_page[purl] = page_prices

        # 3. Copyright year freshness
        year_matches = re.findall(r"(?:©|&copy;|copyright)\s*(?:20\d{2}\s*-\s*)?(20\d{2})", all_text, re.I)
        for y in year_matches:
            if int(y) < CURRENT_YEAR - 2:
                findings.append(make_finding("STALE_AUTHORITATIVE_FACT", f"Stale copyright year {y} on {purl}", "low", purl, f"Copyright year {y} indicates unmaintained content."))

    # Detect Cross-Page Price Conflicts
    all_normalized_prices = set()
    conflicts: List[Dict[str, Any]] = []
    for _u, plist in prices_by_page.items():
        for item in plist:
            all_normalized_prices.add((item["price"], item["currency"], item["interval"]))

    # If different pages list conflicting prices for what appears to be the same tier/product
    distinct_prices = sorted(list({p[0] for p in all_normalized_prices}))
    if len(distinct_prices) > 1:
        # Check if conflicting prices occur across pages
        urls_with_prices = [u for u, pl in prices_by_page.items() if pl]
        if len(urls_with_prices) >= 2:
            p1 = prices_by_page[urls_with_prices[0]][0]["price"]
            p2 = prices_by_page[urls_with_prices[1]][0]["price"]
            if p1 != p2:
                conflict_msg = f"Contradictory prices detected between {urls_with_prices[0]} (${p1}) and {urls_with_prices[1]} (${p2})."
                findings.append(make_finding("FIRST_PARTY_FACT_CONFLICT", "Cross-page price contradiction detected", "critical", urls_with_prices[0], conflict_msg))
                conflicts.append({"urls": urls_with_prices[:2], "prices": [p1, p2]})

    if attribute == "pricing":
        findings = [f for f in findings if f["cause_id"] in ("FIRST_PARTY_FACT_CONFLICT", "CONFLICTING_COMMERCIAL_TERMS")]

    res: Dict[str, Any] = {
        "status": "ok",
        "telemetry": {
            "fact_ledger_size": len(fact_ledger),
            "distinct_prices_count": len(distinct_prices),
            "contradictions_count": len(conflicts),
            "pages_with_pricing": len([u for u, pl in prices_by_page.items() if pl]),
        },
        "findings": findings,
        "recommendations": recommendations,
    }

    if compare_urls and len(compare_urls) >= 2:
        u1, u2 = compare_urls[0], compare_urls[1]
        res["url_comparison"] = {
            "url1": u1,
            "url2": u2,
            "url1_facts": prices_by_page.get(u1, []),
            "url2_facts": prices_by_page.get(u2, []),
        }

    if query:
        matches = [f for f in fact_ledger if query.lower() in str(f).lower()]
        res["query_matches"] = matches

    return res


def main():
    parser = argparse.ArgumentParser(description="Fact Consistency & Lifecycle Diagnostic Sensor")
    parser.add_argument("--site", "-s", default=None)
    parser.add_argument("--inventory", "-i", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--attribute", choices=["pricing", "contact", "dates", "availability"])
    parser.add_argument("--compare-urls", nargs=2, help="Compare facts between two specific URLs")
    parser.add_argument("--query", help="Query facts by keyword")
    parser.add_argument("--conflict-only", action="store_true", help="Filter for only conflict findings")
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
    res = audit(base, domain, inv=inv, state_file=args.state, attribute=args.attribute, compare_urls=args.compare_urls, query=args.query)
    out = json.dumps(res, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
