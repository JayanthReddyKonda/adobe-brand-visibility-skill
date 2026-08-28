#!/usr/bin/env python3
"""
discoverability_check.py - Access & discovery layer of the Brand AI-Readiness Audit.

Evidence hierarchy: L1 direct HTTP/DOM evidence only.
Crawler matrix semantics:
  - 'retrieval' crawlers affect live citations in AI search (blocking is a critical/high defect).
  - 'training' crawlers affect model training/grounding (blocking is an intentional opt-out, not a retrieval defect).
  - 'user_fetch' tokens represent on-demand user browsing actions.
"""
import sys
import os
import re
import json
import argparse
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

# Import safe_fetch from orchestrator if available, or define fallback
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

    def safe_check_status(url, timeout=5, max_bytes=65536, user_agent=DEFAULT_USER_AGENT):
        status, _, _, _ = safe_fetch(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent, method="GET")
        return status

AI_BOTS = [
    "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "anthropic-ai",
    "ChatGPT-User",
    "GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot"
]

CRAWLER_SEMANTICS = {
    "OAI-SearchBot": {"role": "retrieval", "platform": "OpenAI / SearchGPT", "impact_desc": "Live web search & citation generation in ChatGPT Search."},
    "Claude-SearchBot": {"role": "retrieval", "platform": "Anthropic / Claude", "impact_desc": "Live web search and real-time grounding in Claude."},
    "PerplexityBot": {"role": "retrieval", "platform": "Perplexity AI", "impact_desc": "Direct citation and source index for Perplexity AI answers."},
    "anthropic-ai": {"role": "retrieval", "platform": "Anthropic", "impact_desc": "Anthropic AI retrieval and search crawler."},
    "ChatGPT-User": {"role": "user_fetch", "platform": "OpenAI", "impact_desc": "On-demand URL fetch triggered directly by an end-user conversation."},
    "GPTBot": {"role": "training", "platform": "OpenAI", "impact_desc": "Model pre-training and offline dataset collection."},
    "ClaudeBot": {"role": "training", "platform": "Anthropic", "impact_desc": "Model training dataset collection for Claude foundation models."},
    "Google-Extended": {"role": "training", "platform": "Google", "impact_desc": "Training token for Gemini and Vertex AI foundation models."},
    "Applebot-Extended": {"role": "training", "platform": "Apple", "impact_desc": "Training data collection for Apple Intelligence models."},
    "CCBot": {"role": "training", "platform": "Common Crawl", "impact_desc": "Open foundation model pre-training corpus."},
}


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
    groups = []
    sitemaps = []
    current = None
    for line in (body or "").splitlines():
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
    """Decide allow/deny for a user-agent + path per RFC 9309 rules.
    Specific user-agent groups take precedence over the generic '*' group."""
    ua = ua.lower()
    specific_rules = []
    wildcard_rules = []

    for g in groups:
        agents = [a.lower() for a in g.get("agents", [])]
        if ua in agents:
            specific_rules.extend(g.get("rules", []))
        elif "*" in agents:
            wildcard_rules.extend(g.get("rules", []))

    # Specific group takes precedence if present; otherwise fall back to wildcard
    rules = specific_rules if specific_rules else wildcard_rules

    best = ("allow", None, -1)
    for k, v in rules:
        if not v:
            continue
        if _pattern_matches(v, path):
            specificity = len(v)
            if k == "allow" and specificity == best[2]:
                best = (k, v, specificity)
            elif specificity > best[2]:
                best = (k, v, specificity)
    return best[0], best[1]


def audit(base, domain, inv=None):
    """Audit access & discovery."""
    findings, recommendations, evidence = [], [], []
    observations, limitations = [], []

    if inv is not None:
        home = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage"), None)
        if not home or not home.get("html"):
            return {"status": "inconclusive", "findings": [], "recommendations": [],
                    "error": "inventory lacks a usable homepage snapshot"}
        status, html, headers = home["status"], home["html"], {}
    else:
        status, html, headers, err = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
    if status is None:
        return {"status": "inconclusive", "findings": [], "recommendations": [],
                "error": f"could not reach {base} (network unreachable or blocked)"}
    if status >= 400:
        findings.append(dict(
            category="access", title=f"Homepage returns HTTP {status}", severity="critical",
            confidence="high", root_cause="The landing page is not retrievable.",
            cause_family="DISCOVERY.ACCESS", cause_id="DISC-HTTP-ERR",
            impact="No retrieval system, and no visitor, can access the site.",
            evidence=f"GET {base}/ returned HTTP {status}.",
            suggested_action=dict(summary="Restore availability of the homepage (HTTP 200).",
                                  priority="critical",
                                  verification=f"Re-request {base}/ and confirm HTTP 200.")))
        return {"status": "ok", "findings": findings, "recommendations": recommendations}

    # robots.txt: per-bot access with RFC 9309 path matching
    if inv is not None and inv.get("robots") is not None:
        r_status, r_body = inv["robots"].get("status"), inv["robots"].get("text") or ""
    else:
        r_status, r_body, _, _ = safe_fetch(base + "/robots.txt", timeout=8, max_bytes=512*1024)
    groups, sitemaps = [], []
    if r_status == 200 and r_body:
        groups, sitemaps = parse_robots(r_body)

    crawler_matrix = {}
    blocked_retrieval = []
    blocked_training = []
    blocked_user_fetch = []

    for bot in AI_BOTS:
        rule, matched = robots_access(groups, bot, "/") if r_status == 200 else ("allow", None)
        meta = CRAWLER_SEMANTICS.get(bot, {"role": "unknown", "platform": "Unknown", "impact_desc": ""})
        role = meta["role"]
        is_disallowed = (rule == "disallow")
        crawler_matrix[bot] = {
            "role": role,
            "platform": meta.get("platform"),
            "disallowed": is_disallowed,
            "deciding_rule": matched,
            "impact": meta.get("impact_desc")
        }
        if is_disallowed:
            if role == "retrieval":
                blocked_retrieval.append(bot)
            elif role == "training":
                blocked_training.append(bot)
            elif role == "user_fetch":
                blocked_user_fetch.append(bot)

    # 1. Blocked retrieval crawlers -> CRITICAL / HIGH defect
    if blocked_retrieval:
        sev = "critical" if any(b in blocked_retrieval for b in ("OAI-SearchBot", "Claude-SearchBot", "PerplexityBot")) else "high"
        findings.append(dict(
            category="access",
            title="robots.txt blocks AI search retrieval crawlers",
            severity=sev,
            confidence="high",
            root_cause="robots.txt rules disallow AI search retrieval crawlers from accessing the site root.",
            cause_family="DISCOVERY.ACCESS",
            cause_id="DISC-ROBOTS-RETRIEVAL-BLOCKED",
            impact="AI assistants (ChatGPT Search, Perplexity, Claude Search) cannot crawl or cite the site's content in real-time answers.",
            evidence=f"robots.txt (HTTP {r_status}) disallows '/' for retrieval crawler(s): {', '.join(blocked_retrieval)}.",
            suggested_action=dict(
                summary="Allow AI search retrieval crawlers (e.g. OAI-SearchBot, Claude-SearchBot, PerplexityBot) to crawl public content.",
                priority=sev,
                verification="Re-fetch robots.txt and verify retrieval crawlers are no longer denied at '/'.")))

    # 2. Blocked training crawlers -> INFORMATIONAL observation (training opt-out)
    if blocked_training:
        observations.append(dict(
            id=f"OBS-{len(observations) + 1:03d}",
            category="governance",
            source={"url": f"{base}/robots.txt", "method": "robots-parser"},
            observation=f"robots.txt disallows training bots: {', '.join(blocked_training)}",
            evidence=f"Intentional AI model training opt-out detected for {len(blocked_training)} crawler token(s). This prevents bulk model pre-training but does not impair live AI search citations.",
            confidence="high"
        ))

    # Multi-UA probe: check if WAF/edge firewall selectively blocks AI retrieval User-Agents
    bot_probe = {}
    for bot in ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot"):
        p_status, _, _, _ = safe_fetch(base + "/", timeout=8, max_bytes=65536,
                                       user_agent=f"Mozilla/5.0 (compatible; {bot}/1.0; +https://agentskills.io)")
        bot_probe[bot] = p_status

    divergent = [f"{b}: HTTP {s}" for b, s in bot_probe.items()
                 if s is not None and s in (403, 401, 503) and status < 400]
    if divergent:
        findings.append(dict(
            category="access",
            title="AI search crawlers receive WAF / edge blocking",
            severity="high",
            confidence="medium",
            root_cause="The edge server/WAF returns 4xx/5xx responses to AI-crawler User-Agent headers while permitting browser requests.",
            cause_family="DISCOVERY.ACCESS",
            cause_id="DISC-WAF-BLOCK",
            impact="Retrieval systems cannot access content even where robots.txt permits access.",
            evidence=f"Browser request returned HTTP {status}; AI search user-agents returned: {'; '.join(divergent)}.",
            suggested_action=dict(
                summary="Review edge WAF and bot mitigation rules to whitelist verified AI search crawlers on public routes.",
                priority="high",
                verification="Send test HTTP GET requests with crawler UA strings and verify HTTP 200 responses.")))

    # Sitemap check
    if not sitemaps and r_status == 200:
        s_status, _, _, _ = safe_fetch(base + "/sitemap.xml", timeout=6, max_bytes=1024*1024)
        if s_status != 200:
            recommendations.append(dict(
                title="Publish an XML sitemap",
                category="discovery",
                rationale=f"No Sitemap declared in robots.txt and {base}/sitemap.xml returned HTTP {s_status}.",
                suggested_action="Publish sitemap.xml with canonical public URLs and declare it in robots.txt."))

    parser = Dom()
    try:
        parser.feed(html)
    except Exception:
        pass

    xrobots = headers.get("X-Robots-Tag", "")
    if "noindex" in ((parser.meta_robots or "") + " " + xrobots).lower():
        findings.append(dict(
            category="access",
            title="Page is marked noindex",
            severity="critical",
            confidence="high",
            root_cause="A robots meta tag or X-Robots-Tag header instructs search and AI indexers to discard the page.",
            cause_family="DISCOVERY.ACCESS",
            cause_id="DISC-NOINDEX",
            impact="The page is excluded from retrieval indexes and will not be cited by AI systems.",
            evidence=f"Directives on {base}/: meta robots='{parser.meta_robots}', X-Robots-Tag='{xrobots}'.",
            suggested_action=dict(
                summary="Remove the noindex directive from public indexable pages.",
                priority="critical",
                verification="Re-fetch and confirm neither directive contains 'noindex'.")))

    if parser.canonical:
        canon = urljoin(base + "/", parser.canonical)
        if canon.rstrip("/") != base.rstrip("/"):
            sitemap_mentions_canon = False
            if sitemaps:
                s_status, s_body, _, _ = safe_fetch(sitemaps[0], timeout=8, max_bytes=2*1024*1024)
                if s_status == 200 and s_body and canon in s_body:
                    sitemap_mentions_canon = True
            if sitemap_mentions_canon:
                findings.append(dict(
                    category="discovery",
                    title="Canonical target consolidates onto different host",
                    severity="medium",
                    confidence="high",
                    root_cause="The site consolidates onto a different canonical host (declared in markup and confirmed by sitemap).",
                    cause_family="DISCOVERY.CANONICAL",
                    cause_id="DISC-CANONICAL-MISMATCH",
                    impact=f"Retrieval systems index {canon} instead of {base}/; references and citations point to the canonical host.",
                    evidence=f"<link rel='canonical' href='{parser.canonical}'> resolves to {canon}; confirmed by sitemap {sitemaps[0]}.",
                    suggested_action=dict(
                        summary="Audit canonical consolidation to ensure intended domain alignment across all brand assets.",
                        priority="medium",
                        verification=f"Confirm internal links and sitemap all use {canon}.")))
            else:
                recommendations.append(dict(
                    title="Verify homepage canonical target",
                    category="discovery",
                    rationale=f"<link rel='canonical'> points to {canon}. If intentional, ensure all internal links and sitemaps align.",
                    suggested_action=f"Confirm {canon} is the intended canonical host."))

    # Rendering risk: raw HTML text extraction
    words = len(" ".join(parser.text).split())
    if words < 30:
        detail = "empty SPA root container detected" if parser.spa_root else "no SPA root marker"
        findings.append(dict(
            category="rendering",
            title="Primary content absent from initial HTML (rendering risk)",
            severity="high",
            confidence="medium",
            root_cause="Content appears to be injected client-side via JavaScript; the initial HTML response contains minimal readable text.",
            cause_family="DISCOVERY.RENDERING",
            cause_id="DISC-CSR-RENDERING-RISK",
            impact="AI retrieval systems that do not execute JavaScript receive an empty page and cannot index or cite the content.",
            evidence=f"Initial HTML of {base}/ carries only {words} words of visible text ({detail}). Verified on raw HTTP response body.",
            suggested_action=dict(
                summary="Ensure primary brand and product copy is present in the initial HTML payload (via SSR, SSG, or pre-rendering).",
                priority="high",
                verification="Fetch raw HTML response and confirm main heading and copy are present without running JavaScript.")))

    internal = [l for l in parser.links if l.startswith("/") or domain in l]
    evidence.append(dict(
        url=base + "/", http_status=status, words=words,
        internal_links=len(internal), robots_status=r_status,
        sitemaps=sitemaps
    ))

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "evidence": evidence,
        "coverage": {
            "homepage_checked": True,
            "robots_checked": r_status == 200,
            "sitemap_declared": bool(sitemaps),
            "crawler_matrix": crawler_matrix,
            "source": "shared-inventory" if inv is not None else "independent-fetch"
        },
        "limitations": ([] if r_status == 200 else [f"robots.txt returned HTTP {r_status}; access rules unverified"])
    }


def main():
    ap = argparse.ArgumentParser(description="Access & discovery audit layer.")
    ap.add_argument("--site", required=True)
    ap.add_argument("--inventory", help="Path to shared site-inventory JSON (from audit-orchestrator)")
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
