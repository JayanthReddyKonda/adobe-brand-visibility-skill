#!/usr/bin/env python3
"""
discoverability_check.py - Access & discovery layer of the Brand AI-Readiness Audit.

Causal Root Causes:
  - DISCOVERY.ACCESS: AI_RETRIEVAL_BLOCKED, NOINDEX_EXCLUSION, WAF_BOT_CHALLENGE
  - DISCOVERY.DISCOVERY_PATH: CANONICAL_FRAGMENTATION, ORPHANED_CONTENT_PATH
  - DISCOVERY.REPRESENTATION_AVAILABILITY: RENDERED_CONTENT_GAP
"""
import sys
import os
import re
import json
import argparse
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

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
    findings, recommendations, observations = [], [], []

    # 1. Fetch Homepage & robots.txt via shared inventory or live probe
    if inv is not None:
        home_page = next((p for p in inv.get("pages", []) if p.get("page_type") == "homepage" and p.get("resource_type", "html") == "html"), None)
        if not home_page and inv.get("pages"):
            home_page = inv["pages"][0]
        status = home_page.get("status") if home_page else None
        html = home_page.get("html", "") if home_page else ""
        headers = {}
        err = None
        r_info = inv.get("robots") or (inv.get("infrastructure") or {}).get("robots") or {}
        r_status = r_info.get("status")
        robots_txt = r_info.get("text")
    else:
        status, html, headers, err = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        r_status, robots_txt, _, _ = safe_fetch(base + "/robots.txt", timeout=8, max_bytes=512*1024)

    if status is None:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not reach {base} ({err or 'network unreachable or blocked'})"
        }

    # HTTP Status Check
    if status >= 400:
        findings.append({
            "category": "crawlability",
            "title": f"HTTP status {status} on root URL",
            "severity": "critical",
            "confidence": "high",
            "root_cause": f"Root landing URL returns HTTP status {status}.",
            "cause_family": "DISCOVERY.ACCESS",
            "cause_id": "AI_RETRIEVAL_BLOCKED",
            "impact": "Search crawlers and AI assistants cannot fetch the site entrypoint.",
            "evidence": f"GET {base}/ returned HTTP {status}.",
            "suggested_action": {
                "summary": "Fix server configuration or routing so the root URL returns HTTP 200.",
                "priority": "critical",
                "verification": f"Send GET {base}/ and confirm HTTP 200 is returned."
            }
        })
        return {"status": "ok", "findings": findings, "recommendations": []}

    # 2. Parse DOM & Inspect Meta Robots / Canonical / Rendering
    dom = Dom()
    try:
        dom.feed(html)
    except Exception:
        pass

    # Meta Robots Check
    meta_rob = (dom.meta_robots or headers.get("x-robots-tag", "")).lower()
    if "noindex" in meta_rob:
        findings.append({
            "category": "indexability",
            "title": "Homepage explicitly excludes indexers (noindex directive)",
            "severity": "critical",
            "confidence": "high",
            "root_cause": "A noindex directive in meta robots or X-Robots-Tag excludes the page from search indexes.",
            "cause_family": "DISCOVERY.ACCESS",
            "cause_id": "NOINDEX_EXCLUSION",
            "impact": "AI assistants and search engines are instructed not to index or cite this page.",
            "evidence": f"Found '{meta_rob}' in meta robots or X-Robots-Tag header.",
            "suggested_action": {
                "summary": "Remove the 'noindex' directive from public landing pages.",
                "priority": "critical",
                "verification": "Inspect response headers and HTML markup to ensure 'noindex' is absent."
            }
        })

    # Canonical Check
    if dom.canonical:
        c_parsed = urlparse(dom.canonical)
        c_host = c_parsed.netloc.lower()
        if c_host and c_host != domain.lower():
            findings.append({
                "category": "canonicalization",
                "title": "Canonical link points to external domain",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "The page's canonical tag points to a different host, fragmenting search authority.",
                "cause_family": "DISCOVERY.DISCOVERY_PATH",
                "cause_id": "CANONICAL_FRAGMENTATION",
                "impact": "Search engines consolidate ranking signals and citations onto the external canonical domain.",
                "evidence": f"Page on {domain} specifies canonical target '{dom.canonical}'.",
                "suggested_action": {
                    "summary": "Set the canonical URL to point to the authoritative URL on the current domain.",
                    "priority": "medium",
                    "verification": f"Verify the <link rel='canonical'> href matches the current domain ({domain})."
                }
            })

    # Initial HTML Text & Rendering Risk Check
    visible_words = len(" ".join(dom.text).split())
    if visible_words < 30 and dom.spa_root:
        findings.append({
            "category": "rendering",
            "title": "Primary copy missing from initial raw HTML (client-side rendering dependency)",
            "severity": "high",
            "confidence": "medium",
            "root_cause": "The initial HTML payload is an unrendered JavaScript single-page application shell containing fewer than 30 words.",
            "cause_family": "DISCOVERY.REPRESENTATION_AVAILABILITY",
            "cause_id": "RENDERED_CONTENT_GAP",
            "impact": "AI retrieval crawlers and summarizers evaluating the raw HTTP response cannot extract content without full browser execution.",
            "evidence": f"Initial HTML contains only {visible_words} visible words and an unrendered SPA container (<div id='root|app'>).",
            "suggested_action": {
                "summary": "Implement server-side rendering (SSR), static site generation (SSG), or dynamic pre-rendering for core text.",
                "priority": "high",
                "verification": "Fetch raw HTML without executing JavaScript and confirm primary headings and body text are present."
            }
        })

    # 3. robots.txt Analysis
    if r_status == 200 and robots_txt:
        groups, sitemaps = parse_robots(robots_txt)
        blocked_retrieval = []
        blocked_training = []

        for bot in AI_BOTS:
            decision, rule = robots_access(groups, bot, "/")
            sem = CRAWLER_SEMANTICS.get(bot, {"role": "general", "impact_desc": ""})
            role = sem["role"]

            if decision == "disallow":
                if role == "retrieval":
                    blocked_retrieval.append((bot, sem["platform"], rule))
                elif role == "training":
                    blocked_training.append((bot, sem["platform"], rule))
                else:
                    observations.append({
                        "observation": f"User-initiated fetch bot '{bot}' is disallowed in robots.txt (rule: Disallow: {rule or '/'}).",
                        "impact": sem["impact_desc"],
                        "role": role
                    })

        # Disallowed retrieval crawlers -> Critical finding
        if blocked_retrieval:
            names = [b[0] for b in blocked_retrieval]
            rules_str = ", ".join(f"{b[0]} (Disallow: {b[2] or '/'})" for b in blocked_retrieval)
            findings.append({
                "category": "crawlability",
                "title": f"AI search retrieval crawlers blocked in robots.txt ({', '.join(names)})",
                "severity": "critical",
                "confidence": "high",
                "root_cause": "robots.txt explicitly disallows AI search retrieval crawlers responsible for live citations.",
                "cause_family": "DISCOVERY.ACCESS",
                "cause_id": "AI_RETRIEVAL_BLOCKED",
                "impact": "The site is excluded from real-time web grounding and citation generation in ChatGPT Search, Claude, and Perplexity.",
                "evidence": f"robots.txt disallows {len(blocked_retrieval)} retrieval crawler(s): {rules_str}.",
                "suggested_action": {
                    "summary": f"Allow AI search retrieval bots ({', '.join(names)}) on public routes in robots.txt.",
                    "priority": "critical",
                    "verification": "Re-fetch robots.txt and verify Allow: / is declared for retrieval crawlers."
                }
            })

        # Disallowed training crawlers -> Informational observation
        if blocked_training:
            names = [b[0] for b in blocked_training]
            rules_str = ", ".join(f"{b[0]} (Disallow: {b[2] or '/'})" for b in blocked_training)
            observations.append({
                "observation": f"Site opts out of AI foundation model training for {len(blocked_training)} crawler(s): {', '.join(names)} ({rules_str}).",
                "impact": "Content is excluded from foundation model pre-training datasets. (This is an intentional governance opt-out, not an AI search retrieval defect).",
                "role": "training"
            })

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "visible_words_initial_html": visible_words,
            "robots_txt_status": r_status,
            "canonical_declared": dom.canonical,
            "meta_robots_declared": dom.meta_robots
        },
        "limitations": [
            "Raw HTML extractability was evaluated directly; JavaScript headless rendering was not executed."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Access & discovery audit layer.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    args = parser.parse_args()
    base, domain = parse_domain(args.site)
    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    res = audit(base, domain, inv=inv)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
