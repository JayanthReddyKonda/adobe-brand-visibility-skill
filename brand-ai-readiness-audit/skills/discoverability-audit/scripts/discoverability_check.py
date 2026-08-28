#!/usr/bin/env python3
"""
discoverability_check.py - Access & discovery layer of the Brand AI-Readiness Audit.

Evidence hierarchy: L1 direct HTTP/DOM evidence only. Heuristics never
exceed LOW severity. Network-inconclusive probes surface status instead of
claims ("inconclusive" never looks like a clean site).
"""
import sys, os, re, json, argparse
import urllib.request, urllib.error
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = {"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0)"}
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
           "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot", "anthropic-ai"]


def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            body = ""
        return e.code, body, dict(e.headers or {})
    except Exception:
        return None, "", {}


class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.skip = [], 0
        self.canonical, self.meta_robots = None, None
        self.links, self.spa_root = [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = tag.lower()
        if t in ("script", "style", "noscript"):
            self.skip += 1
        if t == "link" and a.get("rel", "").lower() == "canonical":
            self.canonical = a.get("href")
        if t == "meta" and a.get("name", "").lower() == "robots":
            self.meta_robots = a.get("content", "")
        if t == "div" and a.get("id") in ("root", "app", "__next"):
            self.spa_root = True
        if t == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())


def parse_domain(site):
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    return f"{p.scheme}://{p.netloc}", p.netloc


def parse_robots(body):
    agents, current, sitemaps = {}, None, []
    for line in body.splitlines():
        line = line.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            current = v.lower()
            agents.setdefault(current, [])
        elif k == "sitemap":
            sitemaps.append(v)
        elif k in ("allow", "disallow") and current is not None:
            agents[current].append((k, v))
    return agents, sitemaps


def audit(base, domain):
    findings, recommendations, evidence = [], [], []
    status, html, headers = fetch(base + "/")
    if status is None:
        return {"status": "inconclusive", "findings": [], "recommendations": [],
                "error": f"could not reach {base} (network unreachable or blocked)"}
    if status >= 400:
        findings.append(dict(
            category="access", title=f"Homepage returns HTTP {status}", severity="critical",
            confidence="high", root_cause="The landing page is not retrievable.",
            impact="No retrieval system, and no visitor, can access the site.",
            evidence=f"GET {base}/ returned HTTP {status}.",
            suggested_action=dict(summary="Restore availability of the homepage (HTTP 200).",
                                  priority="critical",
                                  verification=f"Re-request {base}/ and confirm HTTP 200.")))
        return {"status": "ok", "findings": findings, "recommendations": recommendations}

    # robots.txt: per-bot access (L1). Absence of a rule = allowed; we only
    # report explicit blanket blocks.
    r_status, r_body, _ = fetch(base + "/robots.txt")
    robots_map, sitemaps = {}, []
    if r_status == 200 and r_body:
        robots_map, sitemaps = parse_robots(r_body)
    blocked = [b for b in AI_BOTS
               if any(k == "disallow" and v == "/" for k, v in robots_map.get(b.lower(), []))]
    if blocked:
        sev = "critical" if any(x in blocked for x in ("GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot")) else "medium"
        findings.append(dict(
            category="access", title="robots.txt blocks AI crawler user-agents", severity=sev,
            confidence="high",
            root_cause="Explicit robots.txt Disallow rules exclude AI retrieval systems from public content.",
            impact="AI assistants that respect robots.txt cannot retrieve or cite the site's content for these user-agents.",
            evidence=f"robots.txt contains 'Disallow: /' for: {', '.join(blocked)}.",
            suggested_action=dict(summary="Remove blanket Disallow rules for AI retrieval user-agents on public content.",
                                  priority=sev,
                                  verification="Re-fetch robots.txt and confirm these user-agents are no longer fully disallowed.")))

    if not sitemaps and r_status == 200:
        s_status, _, _ = fetch(base + "/sitemap.xml")
        if s_status != 200:
            recommendations.append(dict(
                title="Publish an XML sitemap",
                rationale=f"No Sitemap directive in robots.txt and {base}/sitemap.xml returned HTTP {s_status}.",
                suggested_action="Publish sitemap.xml and declare it in robots.txt."))

    parser = Dom()
    try:
        parser.feed(html)
    except Exception:
        pass

    xrobots = headers.get("X-Robots-Tag", "")
    if "noindex" in ((parser.meta_robots or "") + " " + xrobots).lower():
        findings.append(dict(
            category="access", title="Page is marked noindex", severity="critical",
            confidence="high",
            root_cause="A robots meta tag or X-Robots-Tag header instructs indexers to discard the page.",
            impact="The page is excluded from indexes and is unlikely to be quoted or cited by AI systems.",
            evidence=f"Directives on {base}/: meta robots='{parser.meta_robots}', X-Robots-Tag='{xrobots}'.",
            suggested_action=dict(summary="Remove the noindex directive from public pages.",
                                  priority="critical",
                                  verification="Re-fetch and confirm neither directive contains 'noindex'.")))

    if parser.canonical:
        canon = urljoin(base + "/", parser.canonical)
        if canon.rstrip("/") != base.rstrip("/"):
            findings.append(dict(
                category="discovery", title="Homepage canonical points elsewhere", severity="medium",
                confidence="high",
                root_cause="The canonical URL declared on the homepage targets a different address.",
                impact="Retrieval systems may consolidate this page under the canonical target.",
                evidence=f"<link rel='canonical' href='{parser.canonical}'> on {base}/ resolves to {canon}.",
                suggested_action=dict(summary="Self-canonicalize if this is the primary domain.",
                                      priority="medium",
                                      verification=f"Re-fetch and confirm canonical matches {base}/.")))

    # Rendering risk: precise about what was verified (initial HTML only).
    words = len(" ".join(parser.text).split())
    if words < 30:
        detail = "empty SPA root container detected" if parser.spa_root else "no SPA root detected"
        findings.append(dict(
            category="rendering", title="Primary content absent from initial HTML (rendering risk)",
            severity="high", confidence="medium",
            root_cause="Content appears to be injected client-side; the initial HTML response carries almost no text.",
            impact="Retrieval systems that do not execute JavaScript (several AI crawlers among them) receive an effectively empty page. Systems that render JS may still succeed - a risk, not a proven outage.",
            evidence=f"Initial HTML of {base}/ contains {words} words of visible text ({detail}). Verified against the raw HTTP response body only; no rendering was performed.",
            suggested_action=dict(summary="Ensure core text is present in the initial HTML response (SSR/SSG/prerendering); rendering choice is an implementation detail, content availability is not.",
                                  priority="high",
                                  verification="Re-fetch raw HTML and confirm primary copy appears in the response body.")))

    internal = [l for l in parser.links if l.startswith("/") or domain in l]
    evidence.append(dict(url=base + "/", http_status=status, words=words,
                         internal_links=len(internal), robots_status=r_status,
                         sitemaps=sitemaps))
    return {"status": "ok", "findings": findings, "recommendations": recommendations,
            "evidence": evidence}


def main():
    ap = argparse.ArgumentParser(description="Access & discovery audit layer.")
    ap.add_argument("--site", required=True)
    args = ap.parse_args()
    base, domain = parse_domain(args.site)
    print(json.dumps(audit(base, domain), indent=2))


if __name__ == "__main__":
    main()

