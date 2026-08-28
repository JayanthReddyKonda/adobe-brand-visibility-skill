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
    """Parse robots.txt into UA-grouped rule lists (RFC 9309-style groups)."""
    groups = []          # list of {"agents": [...], "rules": [(k, v), ...]}
    sitemaps = []
    current = None
    for line in body.splitlines():
        line = line.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if current is None or current["rules"]:
                current = {"agents": [], "rules": []}
                groups.append(current)
            current["agents"].append(v.lower())
        elif k == "sitemap":
            sitemaps.append(v)
        elif k in ("allow", "disallow") and current is not None:
            current["rules"].append((k, v))
    return groups, sitemaps


def _pattern_matches(pattern, path):
    """RFC 9309 path matching: '*' wildcard, '$' anchor, longest-match."""
    pat = re.escape(pattern).replace(r"\*", ".*")
    if pat.endswith(r"\$"):
        pat = pat[:-2] + "$"
    return re.match(pat, path) is not None


def robots_access(groups, ua, path="/"):
    """Decide allow/deny for a user-agent + path. Returns the deciding rule
    ('allow'/'disallow', value) or ('allow', None) when no rule applies.
    Longest matching rule wins; 'allow' wins ties (per RFC 9309)."""
    ua = ua.lower()
    rules = []
    for g in groups:
        if "*" in g["agents"] or ua in g["agents"]:
            rules.extend(g["rules"])
    best = ("allow", None, -1)
    for k, v in rules:
        if not v:
            continue
        if _pattern_matches(v, path):
            specificity = len(v)
            # 'allow' wins equal-length ties
            if k == "allow" and specificity == best[2]:
                best = (k, v, specificity)
            elif specificity > best[2]:
                best = (k, v, specificity)
    return best[0], best[1]


def audit(base, domain, inv=None):
    """Audit access & discovery. When `inv` (shared site inventory JSON from
    the orchestrator) is supplied, its homepage HTML and robots.txt are used
    instead of re-fetching — all specialists then operate on the same
    evidence snapshot."""
    findings, recommendations, evidence = [], [], []
    if inv is not None:
        home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
        if not home or not home.get("html"):
            return {"status": "inconclusive", "findings": [], "recommendations": [],
                    "error": "inventory lacks a usable homepage snapshot"}
        status, html, headers = home["status"], home["html"], {}
    else:
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

    # robots.txt: per-bot access with real path matching (RFC 9309-style).
    # Absence of a rule = allowed; only explicit blanket denials are reported.
    if inv is not None and inv.get("robots") is not None:
        r_status, r_body = inv["robots"].get("status"), inv["robots"].get("text") or ""
    else:
        r_status, r_body, _ = fetch(base + "/robots.txt")
    groups, sitemaps = [], []
    if r_status == 200 and r_body:
        groups, sitemaps = parse_robots(r_body)
    blocked = [b for b in AI_BOTS
               if robots_access(groups, b, "/")[0] == "disallow"]
    if blocked:
        sev = "critical" if any(x in blocked for x in ("GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot")) else "medium"
        findings.append(dict(
            category="access", title="robots.txt blocks AI crawler user-agents", severity=sev,
            confidence="high",
            root_cause="robots.txt matching rules exclude AI retrieval systems from the site root.",
            impact="AI assistants that respect robots.txt cannot retrieve or cite the site's content for these user-agents.",
            evidence=f"robots.txt (HTTP {r_status}) longest-match Deny rules apply to '/' for: {', '.join(blocked)}.",
            suggested_action=dict(summary="Remove blanket Disallow rules for AI retrieval user-agents on public content.",
                                  priority=sev,
                                  verification="Re-fetch robots.txt and confirm these user-agents are no longer denied at '/'.")))

    # Multi-UA probe: distinguish "whole site blocks this client" from
    # "AI crawler is selectively blocked". Only acts on divergence.
    bot_probe = {}
    for bot in ("GPTBot", "ClaudeBot", "PerplexityBot"):
        req = urllib.request.Request(base + "/", headers={"User-Agent": f"Mozilla/5.0 (compatible; {bot}/1.0)"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                bot_probe[bot] = resp.status
        except urllib.error.HTTPError as e:
            bot_probe[bot] = e.code
        except Exception:
            bot_probe[bot] = None
    divergent = [f"{b}: HTTP {s}" for b, s in bot_probe.items()
                 if s is not None and s >= 403 and status < 400]
    if divergent:
        findings.append(dict(
            category="access", title="AI crawler user-agents receive different treatment than browser requests",
            severity="high", confidence="medium",
            root_cause="The server responds differently to AI-crawler User-Agent strings than to browser requests (WAF/bot filtering or UA rules).",
            impact="AI retrieval systems may be blocked even where robots.txt permits access; content is unreachable to those systems regardless of directives.",
            evidence=f"Browser request: HTTP {status}; bot-UA requests: {'; '.join(divergent)}.",
            suggested_action=dict(summary="Review WAF/bot-mitigation rules to permit verified AI retrieval crawlers on public content.",
                                  priority="high",
                                  verification="Re-issue requests with the listed user-agents and confirm HTTP 200.")))

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
            # Canonical is a hint, not a verdict. Only a finding when
            # corroborated by sitemap disagreement; otherwise informational.
            sitemap_mentions_canon = False
            if sitemaps:
                s_status, s_body, _ = fetch(sitemaps[0])
                if s_status == 200 and s_body and canon in s_body:
                    sitemap_mentions_canon = True
            if sitemap_mentions_canon:
                findings.append(dict(
                    category="discovery", title="Consistent canonical target differs from requested host",
                    severity="medium", confidence="high",
                    root_cause="The site consolidates onto a different canonical host (declared in markup and confirmed by the sitemap).",
                    impact=f"Retrieval systems may index {canon} instead of {base}/; audits and citations must reference the canonical host.",
                    evidence=f"<link rel='canonical' href='{parser.canonical}'> on {base}/ resolves to {canon}; sitemap {sitemaps[0]} lists {canon}.",
                    suggested_action=dict(summary="Use the canonical host consistently in all references and re-audit against it.",
                                          priority="medium",
                                          verification=f"Confirm internal links and sitemap all use {canon}.")))
            else:
                recommendations.append(dict(
                    title="Verify homepage canonical target",
                    rationale=f"<link rel='canonical'> on {base}/ points to {canon}. A differing canonical can be intentional (e.g. www vs apex); no corroborating signal was found, so no defect is asserted.",
                    suggested_action=f"Confirm {canon} is the intended primary host and that redirects, sitemap, and internal links agree with it."))

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
            "evidence": evidence,
            "coverage": {"homepage_checked": True, "robots_checked": r_status == 200,
                         "sitemap_declared": bool(sitemaps),
                         "source": "shared-inventory" if inv is not None else "independent-fetch"},
            "limitations": ([] if r_status == 200 else
                            ["robots.txt not retrievable (HTTP %s); access rules unverified" % r_status])}


def main():
    ap = argparse.ArgumentParser(description="Access & discovery audit layer.")
    ap.add_argument("--site", required=True)
    ap.add_argument("--inventory", help="Path to shared site-inventory JSON (from audit-orchestrator); use its snapshot instead of re-fetching")
    args = ap.parse_args()
    base, domain = parse_domain(args.site)
    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    print(json.dumps(audit(base, domain, inv=inv), indent=2))


if __name__ == "__main__":
    main()

