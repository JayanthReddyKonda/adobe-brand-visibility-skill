#!/usr/bin/env python3
"""
corroboration_check.py - Cross-web authority & corroboration audit layer.

Causal Root Causes:
  - AUTHORITY.IDENTITY_CORROBORATION: BROKEN_AUTHORITY_ANCHOR
  - AUTHORITY.CLAIM_CORROBORATION: CLAIM_CORROBORATION_GAP
"""
import sys
import os
import json
import argparse
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
            return e.code, "", dict(e.headers or {}), str(e)
        except Exception as e:
            return None, "", {}, str(e)


class SameAsExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json_ld = False
        self.json_ld_contents = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            if "application/ld+json" in attr_dict.get("type", "").lower():
                self.in_json_ld = True

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            self.in_json_ld = False

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())


def extract_sameas_links(html):
    """Extract sameAs URLs from JSON-LD blocks."""
    parser = SameAsExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    links = set()
    for raw in parser.json_ld_contents:
        try:
            data = json.loads(raw)
            objs = data if isinstance(data, list) else [data]
            if isinstance(data, dict) and "@graph" in data:
                objs = data["@graph"]
            for o in objs:
                if isinstance(o, dict) and "sameAs" in o:
                    s = o["sameAs"]
                    if isinstance(s, list):
                        for u in s:
                            if isinstance(u, str) and u.startswith("http"):
                                links.add(u.strip())
                    elif isinstance(s, str) and s.startswith("http"):
                        links.add(s.strip())
        except Exception:
            pass
    return sorted(links)


def audit(base, domain, inv=None):
    findings = []
    recommendations = []
    observations = []

    # 1. Fetch Homepage
    if inv is not None:
        home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
        html = home.get("html") if home else None
    else:
        status, html, _, err = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if not html:
            return {
                "status": "inconclusive",
                "findings": [],
                "recommendations": [],
                "error": f"could not reach {base}: {err}"
            }

    if not html:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve content from {base}"
        }

    sameas_urls = extract_sameas_links(html)

    # 2. Check declared authority links
    if not sameas_urls:
        recommendations.append({
            "title": "Declare authoritative identity links (sameAs)",
            "category": "corroboration",
            "rationale": "No sameAs links were declared in JSON-LD. Declaring links to Wikidata, Wikipedia, Crunchbase, or official profiles helps AI models verify brand identity against independent authorities.",
            "suggested_action": "Add sameAs URLs to the Organization JSON-LD markup pointing to official profiles and third-party registries."
        })
        return {
            "status": "ok",
            "findings": [],
            "recommendations": recommendations,
            "observations": observations,
            "coverage": {"sameas_count": 0, "probed": 0},
            "limitations": []
        }

    # 3. Probe up to 5 declared links
    checked = []
    broken = []
    for u in sameas_urls[:5]:
        status, _, headers, err = safe_fetch(u, timeout=5, max_bytes=512*1024, method="GET")
        res_entry = {"url": u, "status": status, "error": err}
        checked.append(res_entry)

        if status is not None and (status >= 400 or status < 200):
            broken.append(f"{u} (HTTP {status})")

    if broken:
        findings.append({
            "category": "corroboration",
            "title": f"Broken authority/profile links declared in sameAs ({len(broken)} link(s))",
            "severity": "medium",
            "confidence": "high",
            "root_cause": "Declared sameAs identity links return HTTP 4xx or 5xx error codes.",
            "cause_family": "AUTHORITY.IDENTITY_CORROBORATION",
            "cause_id": "BROKEN_AUTHORITY_ANCHOR",
            "impact": "AI models attempting to verify entity identity against independent authorities encounter broken links, reducing confidence.",
            "evidence": f"Declared sameAs links returned error status: {'; '.join(broken)}.",
            "suggested_action": {
                "summary": "Update or remove broken sameAs URLs in Organization JSON-LD markup.",
                "priority": "medium",
                "verification": "Confirm all declared sameAs URLs return HTTP 200."
            }
        })

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "sameas_count": len(sameas_urls),
            "probed": len(checked),
            "results": checked
        },
        "limitations": [
            "Probed declared sameAs authority URLs; full web-wide claim corroboration was bounded to declared links."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Cross-web authority & corroboration audit layer.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
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
    print(json.dumps(audit(base, p.netloc, inv=inv), indent=2))


if __name__ == "__main__":
    main()
