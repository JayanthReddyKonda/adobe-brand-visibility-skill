#!/usr/bin/env python3
"""
corroboration_check.py - Cross-web authority & corroboration layer.

Verifies that the identity links a site declares (sameAs, canonical domain,
social profiles) actually resolve, and surfaces corroboration gaps as
recommendations - never as defects, unless a declared authority link is
provably broken (a real inconsistency, L1 evidence).
"""
import sys, json, argparse
import urllib.request, urllib.error
from urllib.parse import urlparse


def status_of(url, timeout=8):
    req = urllib.request.Request(
        url, method="HEAD",
        headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, url
    except Exception:
        # HEAD may be refused; retry with GET
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0)"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, url
        except Exception:
            return None, url


def extract_links(site):
    """Pull sameAs/authoritative links from Organization JSON-LD on the homepage.
    Returns (base, links_or_None, reachable)."""
    import re
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    try:
        with urllib.request.urlopen(urllib.request.Request(base + "/", headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0)"}), timeout=10) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return base, None, False
    links = []
    for raw in re.findall(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(raw)
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for o in objs:
            if isinstance(o, dict):
                sa = o.get("sameAs") or []
                links.extend(sa if isinstance(sa, list) else [sa])
    return base, links or None, True


def audit(site):
    findings, recommendations = [], []
    base, same_links, reachable = extract_links(site)
    if not reachable:
        return {"status": "inconclusive", "findings": [], "recommendations": [],
                "error": f"could not reach {base} (network unreachable or blocked)"}
    checked = []
    if same_links:
        broken = []
        for link in same_links:
            code, final = status_of(link)
            checked.append(dict(url=link, http_status=code))
            if code is None:
                continue  # inconclusive, never a claim
            if code in (301, 302, 308) or code >= 400:
                broken.append(dict(url=link, http_status=code))
        if broken:
            findings.append(dict(
                category="corroboration", title="Declared authority links do not resolve",
                severity="medium", confidence="high",
                root_cause="sameAs/profile URLs in structured data point at pages that redirect away or no longer exist.",
                impact="Broken identity links weaken machine-verifiable corroboration of the brand entity.",
                evidence="; ".join(f"{b['url']} -> HTTP {b['http_status']}" for b in broken),
                suggested_action=dict(
                    summary="Update or remove dead/redirecting sameAs URLs so they land directly on live canonical profiles.",
                    priority="medium",
                    verification="Re-run HEAD checks; every sameAs URL should return 200.")))
    else:
        recommendations.append(dict(
            title="Declare verifiable third-party identities",
            rationale="No sameAs links were found, so AI systems have no machine-checkable path from this site to independent authorities (Wikidata, registries, official profiles). This is a gap, not a proven defect.",
            suggested_action="Add sameAs URLs to Organization JSON-LD pointing at live, authoritative profiles."))
    return {"status": "ok", "findings": findings, "recommendations": recommendations,
            "links_checked": checked}


def main():
    ap = argparse.ArgumentParser(description="Cross-web authority & corroboration audit layer.")
    ap.add_argument("--site", required=True)
    args = ap.parse_args()
    print(json.dumps(audit(args.site), indent=2))


if __name__ == "__main__":
    main()
