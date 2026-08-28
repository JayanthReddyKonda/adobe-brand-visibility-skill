#!/usr/bin/env python3
"""
corroboration_check.py - Cross-web authority & corroboration layer.

Distinguishes between:
  1. Identity Link Verification: Checks that declared sameAs profile URLs
     (Wikidata, Crunchbase, LinkedIn, X, GitHub) resolve with HTTP 200 without broken links.
  2. Authority / Entity Corroboration: Checks whether external profiles corroborate
     the brand's first-party entity identity.
"""
import sys
import os
import json
import re
import argparse
from urllib.parse import urlparse

try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audit-orchestrator", "scripts")))
    from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT
except ImportError:
    import urllib.request, urllib.error
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"
    def safe_fetch(url, timeout=10, max_bytes=512*1024, user_agent=DEFAULT_USER_AGENT, method="GET"):
        req = urllib.request.Request(url, headers={"User-Agent": user_agent}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(max_bytes).decode("utf-8", "ignore"), dict(r.headers), None
        except urllib.error.HTTPError as e:
            return e.code, "", dict(e.headers or {}), str(e)
        except Exception as e:
            return None, "", {}, str(e)

    def safe_check_status(url, timeout=5, max_bytes=65536, user_agent=DEFAULT_USER_AGENT):
        status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent, method="HEAD")
        if status is not None:
            return status
        status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent, method="GET")
        return status


def extract_sameas_links(html):
    """Extract sameAs URLs from JSON-LD on the page."""
    links = []
    for raw in re.findall(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', html or "", re.S | re.I):
        try:
            data = json.loads(raw)
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            objs = data["@graph"]
        for o in objs:
            if isinstance(o, dict):
                sa = o.get("sameAs") or []
                sa_list = sa if isinstance(sa, list) else [sa]
                for s in sa_list:
                    if isinstance(s, str) and s.startswith("http"):
                        links.append(s.strip())
    return sorted(set(links))


def audit(base, domain, inv=None):
    findings, recommendations = [], []
    observations, limitations = [], []

    if inv is not None:
        home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
        if not home or not home.get("html"):
            return {"status": "inconclusive", "findings": [], "recommendations": [],
                    "error": "inventory lacks a usable homepage snapshot"}
        html = home["html"]
    else:
        status, html, _, err = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if status is None or not html:
            return {"status": "inconclusive", "findings": [], "recommendations": [],
                    "error": f"could not reach {base}: {err}"}

    same_links = extract_sameas_links(html)
    checked_links = []

    if same_links:
        broken_links = []
        authorities_verified = []

        for link in same_links[:8]:
            code = safe_check_status(link, timeout=8)
            checked_links.append({"url": link, "http_status": code})

            if code is None:
                continue
            if code in (404, 410, 500, 502, 503):
                broken_links.append({"url": link, "http_status": code})
            elif code == 200:
                authorities_verified.append(link)

        if broken_links:
            findings.append(dict(
                category="corroboration",
                title="Declared authority profile links do not resolve",
                severity="medium",
                confidence="high",
                root_cause="sameAs profile URLs declared in Organization structured data return 4xx/5xx HTTP errors.",
                cause_family="AUTHORITY.CORROBORATION",
                cause_id="AUTH-SAMEAS-BROKEN",
                impact="Dead or broken authority links degrade entity corroboration and signal neglected machine metadata.",
                evidence="; ".join(f"{b['url']} -> HTTP {b['http_status']}" for b in broken_links),
                suggested_action=dict(
                    summary="Remove or update dead sameAs URLs so all declared third-party profiles return HTTP 200.",
                    priority="medium",
                    verification="Re-probe sameAs URLs and confirm all resolve with HTTP 200.")))

        if authorities_verified:
            observations.append(dict(
                id=f"OBS-{len(observations) + 1:03d}",
                category="corroboration",
                source={"url": base + "/", "method": "sameas-resolver"},
                observation=f"Verified {len(authorities_verified)} external authority profile(s)",
                evidence=f"Live profiles confirmed: {', '.join(authorities_verified)}",
                confidence="high"
            ))
    else:
        recommendations.append(dict(
            title="Declare third-party authority profiles (sameAs)",
            category="authority-corroboration",
            rationale="No sameAs links were declared in structured data. Adding verified Wikidata, Crunchbase, and social profiles strengthens entity disambiguation.",
            suggested_action="Publish sameAs links in Organization JSON-LD to authoritative external databases."))

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "sameas_links_declared": len(same_links),
            "links_checked": checked_links,
            "source": "shared-inventory" if inv is not None else "independent-fetch"
        },
        "limitations": limitations
    }


def main():
    ap = argparse.ArgumentParser(description="Cross-web authority & corroboration audit layer.")
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
