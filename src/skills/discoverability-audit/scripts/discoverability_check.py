#!/usr/bin/env python3
"""
discoverability_check.py - Access & discovery layer of the Brand AI-Readiness Audit.

Causal Root Causes:
  - DISCOVERY.ACCESS: AI_RETRIEVAL_BLOCKED, NOINDEX_EXCLUSION, WAF_BOT_CHALLENGE
  - DISCOVERY.DISCOVERY_PATH: CANONICAL_FRAGMENTATION, ORPHANED_CONTENT_PATH
  - DISCOVERY.REPRESENTATION_AVAILABILITY: RENDERED_CONTENT_GAP
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore

AI_BOTS = [
    "OAI-SearchBot",
    "Claude-SearchBot",
    "anthropic-ai",
    "PerplexityBot",
    "Amazonbot",
    "cohere-ai",
    "Meta-ExternalAgent",
    "Claude-User",
    "Perplexity-User",
    "ChatGPT-User",
    "GPTBot",
    "ClaudeBot",
    "Bytespider",
    "Applebot-Extended",
    "Google-Extended",
    "CCBot",
]

CRAWLER_SEMANTICS = {
    "OAI-SearchBot": {
        "role": "retrieval",
        "platform": "OpenAI / SearchGPT",
        "impact_desc": "Live web search & citation generation in ChatGPT Search.",
    },
    "Claude-SearchBot": {
        "role": "retrieval",
        "platform": "Anthropic / Claude",
        "impact_desc": "Live web search and real-time grounding in Claude.",
    },
    "anthropic-ai": {
        "role": "retrieval",
        "platform": "Anthropic / Claude",
        "impact_desc": "Anthropic live retrieval and user-directed web access.",
    },
    "PerplexityBot": {
        "role": "retrieval",
        "platform": "Perplexity AI",
        "impact_desc": "Direct citation and source index for Perplexity AI answers.",
    },
    "Amazonbot": {
        "role": "retrieval",
        "platform": "Amazon / Rufus",
        "impact_desc": "E-commerce conversational search and product recommendation in Amazon Rufus.",
    },
    "cohere-ai": {
        "role": "retrieval",
        "platform": "Cohere / Coral",
        "impact_desc": "Enterprise conversational search and RAG retrieval in Cohere.",
    },
    "Meta-ExternalAgent": {
        "role": "retrieval",
        "platform": "Meta AI",
        "impact_desc": "Live web retrieval for Meta AI assistant and Llama models.",
    },
    "Claude-User": {
        "role": "user_fetch",
        "platform": "Anthropic / Claude",
        "impact_desc": "User-directed web fetch via Claude.",
    },
    "Perplexity-User": {
        "role": "user_fetch",
        "platform": "Perplexity AI",
        "impact_desc": "User-directed web fetch via Perplexity.",
    },
    "ChatGPT-User": {
        "role": "user_fetch",
        "platform": "OpenAI",
        "impact_desc": "On-demand URL fetch triggered directly by an end-user conversation.",
    },
    "GPTBot": {
        "role": "training",
        "platform": "OpenAI",
        "impact_desc": "Model pre-training and offline dataset collection.",
    },
    "ClaudeBot": {
        "role": "training",
        "platform": "Anthropic",
        "impact_desc": "Model training dataset collection for Claude foundation models.",
    },
    "Bytespider": {
        "role": "training",
        "platform": "ByteDance",
        "impact_desc": "Model pre-training and offline dataset collection.",
    },
    "Google-Extended": {
        "role": "training",
        "platform": "Google",
        "impact_desc": "Training token for Gemini and Vertex AI foundation models (robots.txt only).",
    },
    "Applebot-Extended": {
        "role": "training",
        "platform": "Apple",
        "impact_desc": "Training data collection for Apple Intelligence models.",
    },
    "CCBot": {
        "role": "training",
        "platform": "Common Crawl",
        "impact_desc": "Open foundation model pre-training corpus.",
    },
}

SPA_ID_PATTERNS = re.compile(
    r"^(root|app|mount|__next|__nuxt|app-root|___gatsby|svelte|svelte-app|react-root|vue-app|app-container|main-app|application)$",
    re.IGNORECASE,
)
SPA_CLASS_PATTERNS = re.compile(
    r"\b(react-root|vue-app|app-container|spa-container|application-root|mount-point)\b", re.IGNORECASE
)
THIRD_PARTY_SCRIPT_PATTERNS = re.compile(
    r"(googletagmanager\.com|google-analytics\.com|analytics\.js|gtag/js|gtm\.js|clarity\.ms|"
    r"hotjar\.com|intercom\.io|facebook\.net|fbevents\.js|segment\.com|stripe\.com|recaptcha|"
    r"polyfill\.io|fontawesome|typekit|fonts\.googleapis\.com|cloudflareinsights\.com|"
    r"cookiebot\.com|onetrust\.com|trustarc\.com|hubspot\.com|hs-scripts\.com|datadoghq)",
    re.IGNORECASE,
)


def is_valid_hreflang(code):
    """Validate the language-region subset supported by HTML hreflang links."""
    normalized = str(code or "").strip().lower()
    if normalized == "x-default":
        return True
    if "_" in normalized or not re.fullmatch(r"[a-z]{2}(?:-[a-z]{2}|-\d{3})?", normalized):
        return False
    return not normalized.endswith("-uk")


class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.skip = [], 0
        self.canonical, self.meta_robots = None, None
        self.canonicals = []
        self.jsonld_blocks = []
        self.in_json_ld = False
        self.hreflangs = []
        self.links = []
        self.spa_root = False
        self.spa_marker_name = None
        self.in_noscript = False
        self.noscript_requires_js = False
        self.app_script_srcs = []
        self.body_content_elements = 0
        self.headings_count = 0
        self.paragraphs_count = 0
        self.in_body = False
        self.current_tag = None
        self.has_main = False
        self.has_article = False
        self.has_header = False
        self.has_nav = False
        self.has_footer = False
        self.has_aside = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = tag.lower()
        self.current_tag = t
        if t == "body":
            self.in_body = True
        if t == "main":
            self.has_main = True
        elif t == "article":
            self.has_article = True
        elif t == "header":
            self.has_header = True
        elif t == "nav":
            self.has_nav = True
        elif t == "footer":
            self.has_footer = True
        elif t == "aside":
            self.has_aside = True
        if self.in_body and t not in ("script", "style", "noscript", "link", "meta", "head"):
            self.body_content_elements += 1
        if t == "script":
            self.skip += 1
            if "application/ld+json" in (a.get("type") or "").lower():
                self.in_json_ld = True
            src = (a.get("src") or "").strip()
            if src and not THIRD_PARTY_SCRIPT_PATTERNS.search(src):
                self.app_script_srcs.append(src)
        elif t == "style":
            self.skip += 1
        elif t == "noscript":
            self.skip += 1
            self.in_noscript = True
        if t == "link" and (a.get("rel") or "").lower() == "alternate" and a.get("hreflang"):
            self.hreflangs.append({"lang": a.get("hreflang"), "href": a.get("href")})
        if t == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href")
            if a.get("href"):
                self.canonicals.append(a.get("href"))
        if t == "meta" and (a.get("name") or "").lower() == "robots":
            self.meta_robots = a.get("content", "")

        # 1. Container ID / Class heuristics
        cid = (a.get("id") or "").strip()
        ccls = (a.get("class") or "").strip()
        if t in ("div", "main", "section"):
            if cid and (
                SPA_ID_PATTERNS.match(cid)
                or re.search(r"(react|vue|angular|svelte|spa)[-_](root|app|container)", cid, re.IGNORECASE)
            ):
                self.spa_root = True
                self.spa_marker_name = f"<{t} id='{cid}'>"
            elif ccls and (
                SPA_CLASS_PATTERNS.search(ccls)
                or re.search(r"(react|vue|angular|svelte)[-_](root|app|container)", ccls, re.IGNORECASE)
            ):
                self.spa_root = True
                self.spa_marker_name = f"<{t} class='{ccls}'>"
        elif t in ("app-root", "app-main", "ng-component", "router-outlet"):
            self.spa_root = True
            self.spa_marker_name = f"<{t}>"
        elif "data-reactroot" in a or "data-v-app" in a or "ng-app" in a:
            self.spa_root = True
            marker_attr = (
                "data-reactroot" if "data-reactroot" in a else ("data-v-app" if "data-v-app" in a else "ng-app")
            )
            self.spa_marker_name = f"<{t} {marker_attr}>"

        if t == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style") and self.skip:
            self.skip -= 1
            if t == "script":
                self.in_json_ld = False
        elif t == "noscript" and self.skip:
            self.skip -= 1
            self.in_noscript = False
        elif t == "body":
            self.in_body = False
        self.current_tag = None

    def handle_data(self, data):
        txt = data.strip()
        if self.in_json_ld and txt:
            self.jsonld_blocks.append(txt)
        if self.in_noscript and re.search(
            r"\b(enable javascript|requires javascript|javascript to run|javascript enabled)\b", data, re.IGNORECASE
        ):
            self.noscript_requires_js = True
        if not self.skip and txt:
            self.text.append(txt)
            if self.current_tag in ("h1", "h2", "h3", "h4"):
                self.headings_count += 1
            elif self.current_tag in ("p", "article", "li", "span"):
                self.paragraphs_count += 1


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
            if (k == "allow" and specificity == best[2]) or specificity > best[2]:
                best = (k, v, specificity)
    return best[0], best[1]


def audit(base, domain, inv=None, state_file=None):
    findings, recommendations, observations = [], [], []

    # 1. Fetch Homepage & robots.txt via shared inventory or live probe
    if inv is not None:
        home_page = next(
            (
                p
                for p in inv.get("pages", [])
                if p.get("page_type") == "homepage" and p.get("resource_type", "html") == "html"
            ),
            None,
        )
        if not home_page and inv.get("pages"):
            home_page = inv["pages"][0]
        status = (
            home_page.get("status")
            or home_page.get("status_code")
            or (200 if (home_page and (home_page.get("html") or home_page.get("raw_html"))) else None)
        ) if home_page else None
        html = (home_page.get("html") or home_page.get("raw_html") or "") if home_page else ""

        headers = home_page.get("headers", {}) if home_page else {}
        if not headers and home_page and home_page.get("content_type"):
            headers = {"content-type": home_page.get("content_type")}
        err = None
        r_info = inv.get("robots") or (inv.get("infrastructure") or {}).get("robots") or {}
        if isinstance(r_info, dict):
            r_status = r_info.get("status")
            robots_txt = r_info.get("text")
        else:
            r_status = None
            robots_txt = None
        # Also check top-level robots_txt string (common inventory format)
        if not robots_txt and isinstance(inv.get("robots_txt"), str):
            robots_txt = inv["robots_txt"]
            r_status = 200
    else:
        status, html, headers, err = safe_fetch(base + "/", timeout=10, max_bytes=2 * 1024 * 1024)
        r_status, robots_txt, _, _ = safe_fetch(base + "/robots.txt", timeout=8, max_bytes=512 * 1024)

    state = {"version": 1, "entities": {}, "facts": {}, "claims": {}, "observations": {}, "page_context": {}}
    if state_file and os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
        except Exception:
            pass

    if status is None:
        if state_file:
            import tempfile as _tf

            _fd, _tmp = _tf.mkstemp(dir=os.path.dirname(os.path.abspath(state_file)))
            with os.fdopen(_fd, "w") as f:
                json.dump(state, f)
            os.replace(_tmp, state_file)
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not reach {base} ({err or 'network unreachable or blocked'})",
        }

    # HTTP Status Check
    if status >= 400:
        findings.append(
            {
                "category": "crawlability",
                "title": f"HTTP status {status} on root URL",
                "severity": "critical",
                "confidence": "high",
                "root_cause": f"Root landing URL returns HTTP status {status}.",
                "cause_family": "DISCOVERY.ACCESS",
                "id": "AI_RETRIEVAL_BLOCKED",
                "cause_id": "AI_RETRIEVAL_BLOCKED",
                "impact": "Search crawlers and AI assistants cannot fetch the site entrypoint.",
                "evidence": f"GET {base}/ returned HTTP {status}.",
                "suggested_action": {
                    "summary": "Fix server configuration or routing so the root URL returns HTTP 200.",
                    "technical_fix": "Configure web server routing, reverse proxy, and CDN origin mapping to return HTTP 200 for root URL.",
                    "creative_fix": "Ensure homepage template renders branded fallbacks with accessible navigation if downstream services fail.",
                    "priority": "critical",
                    "verification": f"Send GET {base}/ and confirm HTTP 200 is returned.",
                },
            }
        )

    # Check Contract C3: Differential AI Crawler Access / WAF Block Probe
    # P1-46: Skip live bot probe when inv is provided (zero redundant crawls)
    if inv is None:
        bot_ua = "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"
        bot_status, _, _, _ = safe_fetch(base + "/", timeout=6, max_bytes=65536, user_agent=bot_ua, method="HEAD")
        if bot_status in (403, 405, 501):
            bot_status, _, _, _ = safe_fetch(base + "/", timeout=6, max_bytes=65536, user_agent=bot_ua, method="GET")
        if bot_status in (403, 401, 503) and status == 200:
            findings.append(
                {
                    "category": "crawlability",
                    "title": "WAF / Server blocks AI search crawlers at HTTP layer",
                    "severity": "critical",
                    "confidence": "high",
                    "root_cause": "The web server or WAF returns HTTP 403/503 specifically when probed with AI search crawler User-Agents.",
                    "cause_family": "DISCOVERY.ACCESS",
                    "id": "AI_RETRIEVAL_BLOCKED",
                    "cause_id": "AI_RETRIEVAL_BLOCKED",
                    "impact": "Real-time AI search assistants (ChatGPT Search) are blocked from fetching site content regardless of robots.txt declarations.",
                    "evidence": f"GET / returned HTTP 200 for standard browsers but HTTP {bot_status} for OAI-SearchBot.",
                    "suggested_action": {
                        "summary": "Configure WAF/CDN security rules (Cloudflare, AWS WAF, Akamai) to allow verified AI search retrieval bots.",
                        "technical_fix": "Update WAF security rules to whitelist verified AI retrieval User-Agents and autonomous search IP ranges.",
                        "creative_fix": "Deploy targeted rate limits instead of outright IP/agent blockades for recognized search assistance bots.",
                        "priority": "critical",
                        "verification": "Probe the root URL with OAI-SearchBot User-Agent and confirm HTTP 200 is returned.",
                    },
                }
            )

    # 2. Parse DOM & Inspect Meta Robots / Canonical / Rendering
    dom = Dom()
    try:
        dom.feed(html)
    except Exception:
        pass

    # Meta Robots Check (Combines <meta name="robots"> and X-Robots-Tag header, checks for noindex and none)
    x_robots = str(headers.get("x-robots-tag", "")).lower()
    meta_tag = str(dom.meta_robots or "").lower()
    raw_directives = re.split(r"[,;\s]+", f"{meta_tag} {x_robots}".strip())
    robot_tokens = {d.strip() for d in raw_directives if d.strip()}
    if "noindex" in robot_tokens or "none" in robot_tokens:
        findings.append(
            {
                "category": "indexability",
                "title": "Homepage explicitly excludes indexers (noindex/none directive)",
                "severity": "critical",
                "confidence": "high",
                "root_cause": "A noindex or none directive in meta robots or X-Robots-Tag excludes the page from search indexes.",
                "cause_family": "DISCOVERY.ACCESS",
                "id": "NOINDEX_EXCLUSION",
                "cause_id": "NOINDEX_EXCLUSION",
                "impact": "AI assistants and search engines are instructed not to index or cite this page.",
                "evidence": f"Found direct exclusion directive in meta robots / X-Robots-Tag ({', '.join(sorted(robot_tokens & {'noindex', 'none'}))}).",
                "suggested_action": {
                    "summary": "Remove the 'noindex' or 'none' directive from public landing pages.",
                    "technical_fix": "Remove <meta name='robots' content='noindex'> tag and X-Robots-Tag: noindex header from public landing page responses.",
                    "creative_fix": "Ensure brand marketing and product discovery copy is configured for full search indexing across CMS templates.",
                    "priority": "critical",
                    "verification": "Inspect response headers and HTML markup to ensure 'noindex' and 'none' are absent.",
                },
            }
        )

    # Check crawled pages for noindex directives if inventory is present
    if inv and inv.get("pages"):
        sub_noindex = []
        for p in inv.get("pages", []):
            pu = p.get("url") or ""
            if pu.rstrip("/") in (base.rstrip("/"), (base + "/").rstrip("/")):
                continue
            p_meta = p.get("robots_meta") or []
            if isinstance(p_meta, str):
                p_meta = [p_meta]
            p_x = p.get("x_robots_tag") or []
            if isinstance(p_x, str):
                p_x = [p_x]
            p_tokens = set()
            for d in list(p_meta) + list(p_x):
                for tok in re.split(r"[,;\s]+", str(d).lower()):
                    if tok:
                        p_tokens.add(tok)
            if p.get("noindex") or ("noindex" in p_tokens or "none" in p_tokens):
                sub_noindex.append(pu)
        if sub_noindex and not any(f.get("cause_id") == "NOINDEX_EXCLUSION" for f in findings):
            findings.append(
                {
                    "category": "indexability",
                    "title": "Sub-pages explicitly exclude indexers (noindex/none directive)",
                    "severity": "high",
                    "confidence": "high",
                    "root_cause": "Sub-pages contain noindex or none directives in robots meta tag or X-Robots-Tag header.",
                    "cause_family": "DISCOVERY.ACCESS",
                    "id": "NOINDEX_EXCLUSION",
                    "cause_id": "NOINDEX_EXCLUSION",
                    "impact": "AI retrieval searchbots cannot index these sub-pages, preventing specific product or content citation.",
                    "evidence": f"Found noindex directive on: {', '.join(sub_noindex[:5])}",
                    "suggested_action": {
                        "summary": "Remove noindex from public pages intended for AI retrieval.",
                        "technical_fix": "Remove <meta name='robots' content='noindex'> tag and X-Robots-Tag: noindex header from public sub-pages.",
                        "creative_fix": "Verify CMS robots configuration for sub-page templates.",
                        "priority": "high",
                        "verification": "Inspect response headers and HTML markup to ensure noindex is absent.",
                    },
                }
            )

    # Hreflang Validation Check across homepage and inventory
    all_hreflangs = list(dom.hreflangs)
    if inv and inv.get("pages"):
        for p in inv.get("pages", []):
            for hl in p.get("hreflangs", []):
                hl_dict = hl if isinstance(hl, dict) else {"lang": getattr(hl, "lang", ""), "href": getattr(hl, "href", "")}
                if hl_dict not in all_hreflangs:
                    all_hreflangs.append(hl_dict)

    if all_hreflangs:
        invalid_langs = []
        for hl in all_hreflangs:
            code = str(hl.get("lang", "")).lower().strip()
            if code and not is_valid_hreflang(code):
                invalid_langs.append(code)

        if invalid_langs:
            findings.append(
                {
                    "category": "locale",
                    "title": "Invalid hreflang ISO codes (locale misconfiguration)",
                    "severity": "medium",
                    "confidence": "high",
                    "root_cause": "The page declares hreflang tags using invalid ISO 639-1 or ISO 3166-1 codes.",
                    "cause_family": "DISCOVERY.DISCOVERY_PATH",
                    "id": "LOCALE_MISCONFIGURATION",
                    "cause_id": "LOCALE_MISCONFIGURATION",
                    "impact": "Search engines and AI indexers may misinterpret the language or regional targeting, surfacing the wrong locale.",
                    "evidence": f"Found invalid hreflang code(s) on {domain}: {', '.join(sorted(set(invalid_langs)))}. (e.g. use 'en' instead of 'eng', 'ja' instead of 'jp', 'GB' instead of 'UK').",
                    "suggested_action": {
                        "summary": "Fix hreflang codes to strictly follow ISO 639-1 (language) and ISO 3166-1 Alpha-2 (region).",
                        "technical_fix": "Update all <link rel='alternate' hreflang='...'> tags to use valid two-letter ISO 639-1 language and ISO 3166-1 region codes.",
                        "creative_fix": "Align localized page messaging with country-specific terminology, currency symbols, and cultural context.",
                        "priority": "medium",
                        "verification": "Verify all <link rel='alternate' hreflang='...'> tags use valid ISO codes.",
                    },
                }
            )

    # AI Discovery & Machine Manifests Observation
    infra = inv.get("infrastructure", {}) if inv else {}
    if infra:
        missing_manifests = []
        if not infra.get("llms_txt", {}).get("present"):
            missing_manifests.append("/llms.txt")
        if not infra.get("pricing_md", {}).get("present"):
            missing_manifests.append("/pricing.md")
        if not infra.get("ai_plugin", {}).get("present"):
            missing_manifests.append("/.well-known/ai-plugin.json")
        if not infra.get("security_txt", {}).get("present"):
            missing_manifests.append("/.well-known/security.txt")
        if missing_manifests:
            observations.append(
                {
                    "check_id": "G1",
                    "title": "Machine discoverability manifests absent",
                    "scope": base + "/",
                    "observation": f"Site does not declare AI discoverability manifests: {', '.join(missing_manifests)}.",
                    "actual_band": "U",
                    "finding_kind": "informational_observation",
                    "limitation": "Optional machine discoverability standard; improves direct AI agent citation and retrieval precision when present.",
                }
            )

    # Canonical Check & B3 Competing Canonicals
    unique_canonicals = sorted(set(c.strip() for c in dom.canonicals if c and c.strip()))
    if len(unique_canonicals) > 1:
        findings.append(
            {
                "category": "canonicalization",
                "title": "Competing HTML canonical declarations",
                "severity": "high",
                "confidence": "high",
                "root_cause": "The page declares multiple competing canonical link tags pointing to different destinations.",
                "cause_family": "DISCOVERY.DISCOVERY_PATH",
                "id": "CANONICAL_FRAGMENTATION",
                "cause_id": "CANONICAL_FRAGMENTATION",
                "check_id": "B3",
                "actual_band": "S3",
                "impact": "Search crawlers and citation engines face conflicting canonical targets and cannot establish the preferred indexing URL.",
                "evidence": f"Multiple competing canonical tags declared: {' | '.join(unique_canonicals)}",
                "suggested_action": {
                    "summary": "Consolidate multiple canonical declarations into a single authoritative URL.",
                    "technical_fix": "Ensure the HTML <head> contains exactly one <link rel='canonical' href='...'> pointing to the definitive canonical URL.",
                    "creative_fix": "Audit header templates, CMS plugins, and layout wrappers to eliminate duplicate canonical injections.",
                    "priority": "high",
                    "verification": "Inspect raw HTML output and confirm exactly one canonical element is present.",
                },
            }
        )
    elif len(unique_canonicals) == 1:
        c_val = unique_canonicals[0]
        c_parsed = urlparse(c_val)
        c_host = c_parsed.netloc.lower()
        if c_host and c_host != domain.lower() and not dom.meta_robots and "noindex" not in (dom.meta_robots or ""):
            observations.append(
                {
                    "check_id": "B3",
                    "title": "Cross-domain canonical observed",
                    "scope": base + "/",
                    "observation": f"Page specifies external canonical target '{c_val}'.",
                    "actual_band": "U",
                    "finding_kind": "informational_observation",
                    "limitation": "External canonicalization may be intentional syndication; verify owner publication intent.",
                }
            )

    # Check E5: Strict JSON-LD Syntax Check
    pages_to_check = [p for p in inv.get("pages", [])] if inv and inv.get("pages") else [{"html": html, "url": base + "/"}]
    for page_idx, page in enumerate(pages_to_check):
        page_html = page.get("html") or page.get("raw_html") or ""
        p_dom = Dom()
        try:
            p_dom.feed(page_html)
        except Exception:
            pass
        for i, block in enumerate(getattr(p_dom, "jsonld_blocks", [])):
            try:
                def _constant(val):
                    raise ValueError(f"Non-JSON numeric constant: {val}")
                json.loads(block, parse_constant=_constant)
            except (ValueError, json.JSONDecodeError) as exc:
                findings.append(
                    {
                        "category": "structured_data",
                        "title": "JSON-LD block cannot be parsed as JSON",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": "A script block declared as application/ld+json contains malformed JSON syntax failing RFC 8259 parsing.",
                        "cause_family": "DISCOVERY.REPRESENTATION_AVAILABILITY",
                        "id": f"E5_MALFORMED_JSONLD_{page_idx}_{i}",
                        "cause_id": "MALFORMED_JSONLD_SYNTAX",
                        "check_id": "E5",
                        "actual_band": "S2",
                        "finding_kind": "confirmed_problem",
                        "impact": "AI search engines, schema extractors, and LLM grounding parsers cannot parse the structured data.",
                        "evidence": f"JSON-LD syntax decode failure: {str(exc)[:160]}",
                        "suggested_action": {
                            "summary": "Repair the JSON syntax of the invalid JSON-LD block to conform to RFC 8259.",
                            "technical_fix": "Validate JSON-LD template output with a strict JSON linter and fix unescaped characters or missing braces.",
                            "creative_fix": "Ensure CMS and structured data plugins emit valid RFC 8259 JSON strings.",
                            "priority": "medium",
                            "verification": "Extract the script block and verify json.loads succeeds without errors.",
                        },
                    }
                )

    # Check B4: Repeated HTTP 404/5xx on observed URLs
    if inv and inv.get("pages"):
        for p in inv.get("pages", []):
            p_status = p.get("status")
            p_url = p.get("url", "")
            if p_status in (404, 410, 500, 502, 504) and p_url:
                findings.append(
                    {
                        "category": "crawlability",
                        "title": f"Repeated HTTP {p_status} on an observed URL",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": f"Observed URL returned HTTP error status {p_status}.",
                        "cause_family": "DISCOVERY.ACCESS",
                        "id": f"B4_{p_status}",
                        "cause_id": "REPEATED_RESOURCE_ERROR",
                        "check_id": "B4",
                        "actual_band": "S2",
                        "finding_kind": "confirmed_problem",
                        "impact": "Error status responses disrupt discovery and waste search engine crawl budgets.",
                        "evidence": f"Observed HTTP {p_status} on {p_url}",
                        "suggested_action": {
                            "summary": f"For {p_url}: Propose a verified equivalent destination if one exists. Otherwise offer restore or remove-reference options.",
                            "technical_fix": f"Repair server routing or set up a 301 permanent redirect for {p_url} to an active equivalent page.",
                            "creative_fix": "Ensure 404 pages provide rich navigation and search affordances for lost visitors.",
                            "priority": "medium",
                            "verification": f"Send HTTP GET to {p_url} and verify HTTP 200 is returned.",
                        },
                    }
                )

    # Check D1: Declared sitemap XML validation
    sitemaps = []
    if inv:
        sitemaps = inv.get("sitemaps", []) or (inv.get("infrastructure", {}) or {}).get("sitemaps", [])
    for sm in sitemaps:
        sm_text = sm.get("text", "") if isinstance(sm, dict) else ""
        sm_url = sm.get("url", "") if isinstance(sm, dict) else (sm if isinstance(sm, str) else "")
        if sm_text:
            if "<!DOCTYPE" in sm_text.upper() or "<!ENTITY" in sm_text.upper():
                continue
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(sm_text)
                if root.tag not in ("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset", "{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex"):
                    raise ValueError(f"Unexpected root tag: {root.tag}")
            except Exception as exc:
                findings.append(
                    {
                        "category": "crawlability",
                        "title": "Declared sitemap is not valid supported sitemap XML",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": f"Declared sitemap XML at {sm_url} failed parsing: {exc}",
                        "cause_family": "DISCOVERY.ACCESS",
                        "id": "D1_INVALID_SITEMAP",
                        "cause_id": "INVALID_SITEMAP_SYNTAX",
                        "check_id": "D1",
                        "actual_band": "S2",
                        "finding_kind": "confirmed_problem",
                        "impact": "Search engine bots fail to parse the sitemap XML and cannot discover declared URLs.",
                        "evidence": f"Sitemap XML parsing failure at {sm_url}: {str(exc)[:160]}",
                        "suggested_action": {
                            "summary": "Ensure the sitemap uses standard sitemap XML format (<urlset> or <sitemapindex> in namespace http://www.sitemaps.org/schemas/sitemap/0.9).",
                            "technical_fix": "Fix sitemap generator to emit valid XML with root <urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>.",
                            "creative_fix": "Ensure sitemap generator software is properly configured and outputs clean XML.",
                            "priority": "medium",
                            "verification": "Validate sitemap XML against standard schema at sitemaps.org.",
                        },
                    }
                )

    # Initial HTML Text & Rendering Risk Check
    visible_words = len(" ".join(dom.text).split())
    has_semantic_content = (dom.headings_count >= 1 and dom.paragraphs_count >= 1) or visible_words >= 15

    # 1. Definite Framework / JS Dependency Shell (recognized framework container or explicit noscript requirement)
    if visible_words < 25 and (dom.spa_root or dom.noscript_requires_js):
        marker = dom.spa_marker_name or "<noscript> (JavaScript requirement notice)"
        findings.append(
            {
                "category": "rendering",
                "title": "Primary copy missing from initial raw HTML (client-side rendering dependency)",
                "severity": "high",
                "confidence": "high" if dom.noscript_requires_js else "medium",
                "root_cause": "The initial HTML payload is an unrendered JavaScript single-page application shell containing fewer than 25 words.",
                "cause_family": "DISCOVERY.REPRESENTATION_AVAILABILITY",
                "id": "RENDERED_CONTENT_GAP",
                "cause_id": "RENDERED_CONTENT_GAP",
                "impact": "Some retrieval clients may receive materially incomplete content from the initial HTML representation.",
                "evidence": f"Initial HTML contains only {visible_words} visible words and an unrendered client-side shell ({marker}).",
                "suggested_action": {
                    "summary": "Implement server-side rendering (SSR), static site generation (SSG), or dynamic pre-rendering for core text.",
                    "technical_fix": "Configure Next.js, Nuxt, or edge pre-rendering to output semantic HTML tags for core copy on initial request.",
                    "creative_fix": "Craft semantic hero titles, introductory paragraphs, and feature highlights that render without client execution.",
                    "priority": "high",
                    "verification": "Fetch raw HTML without executing JavaScript and confirm primary headings and body text are present.",
                },
            }
        )
    # 2. Circumstantial Structural Fallback (NO framework marker, but empty body with app scripts and NO semantic content)
    elif (
        visible_words < 12
        and len(dom.app_script_srcs) >= 1
        and dom.body_content_elements <= 3
        and not has_semantic_content
        and not dom.spa_root
    ):
        findings.append(
            {
                "category": "rendering",
                "title": "Primary copy missing from initial raw HTML (unrendered application bundle)",
                "severity": "medium",
                "confidence": "medium",
                "root_cause": "The initial HTML body contains minimal copy and an application JavaScript bundle without pre-rendered semantic content.",
                "cause_family": "DISCOVERY.REPRESENTATION_AVAILABILITY",
                "id": "RENDERED_CONTENT_GAP",
                "cause_id": "RENDERED_CONTENT_GAP",
                "impact": "AI retrieval crawlers may receive an unrendered page shell if the page relies on client-side mounting.",
                "evidence": f"Initial HTML contains only {visible_words} visible words, no semantic headings/paragraphs, and {len(dom.app_script_srcs)} application script(s).",
                "suggested_action": {
                    "summary": "Ensure critical landing copy is pre-rendered in the initial HTML payload.",
                    "technical_fix": "Pre-render core page copy into the initial HTML document body before hydrating client-side bundles.",
                    "creative_fix": "Provide meaningful brand summary copy in the static fallback shell for non-JS crawlers.",
                    "priority": "medium",
                    "verification": "Fetch raw HTML without JavaScript execution and verify primary content is present.",
                },
            }
        )

    # 3. Multi-Page Client-Side Rendering Shell Check on Commercial/Catalog Routes
    if not any(f.get("cause_id") == "RENDERED_CONTENT_GAP" for f in findings) and inv:
        unrendered_pages = []
        for p in inv.get("pages", []):
            p_url = p.get("url", "")
            p_html = p.get("html", "")
            p_type = p.get("page_type", "")
            if not p_html or p_type == "homepage":
                continue
            p_words = p.get("word_count", 0)
            if p_words < 25 and (
                "<script type=\"importmap\"" in p_html
                or 'type="module"' in p_html
                or 'id="root"' in p_html
                or 'id="app"' in p_html
                or "storefront-" in p_html
                or "<noscript" in p_html
            ):
                unrendered_pages.append((p_url, p_words, p_type))

        if unrendered_pages:
            def _rep_priority(item):
                u, w, pt = item
                u_lower = u.lower()
                penalty = 0
                if "/drafts/" in u_lower:
                    penalty += 1000
                if "/content/dam/" in u_lower or "/dam/" in u_lower:
                    penalty += 500
                if "/quiz/" in u_lower or "quiz" in u_lower:
                    penalty += 300
                if any(frag in u_lower for frag in ("/nav", "/footer", "/header", "/sidebar")):
                    penalty += 200
                type_rank = {
                    "product_detail": 10,
                    "product": 15,
                    "pricing": 20,
                    "category": 30,
                    "catalog": 35,
                    "article": 40,
                    "general": 50,
                }
                base_prio = type_rank.get(pt, 60)
                if any(k in u_lower for k in ("/product", "/shop", "/item", "/store")):
                    base_prio -= 5
                elif any(k in u_lower for k in ("/coffee", "/tea", "/machines", "/accessories")):
                    base_prio -= 3
                return (penalty, base_prio, len(u))

            unrendered_pages.sort(key=_rep_priority)
            rep_url, rep_words, rep_type = unrendered_pages[0]
            display_type = f"{rep_type} routes" if rep_type and rep_type not in ("general", "unknown") else "core routes"
            findings.append(
                {
                    "category": "rendering",
                    "title": f"Primary copy missing from initial raw HTML (client-side rendering gap on {display_type})",
                    "severity": "high",
                    "confidence": "high",
                    "root_cause": f"RENDERED_CONTENT_GAP: Page {rep_url} serves an unrendered client-side JavaScript shell containing only {rep_words} words.",
                    "cause_family": "DISCOVERY.REPRESENTATION_AVAILABILITY",
                    "id": "RENDERED_CONTENT_GAP",
                    "cause_id": "RENDERED_CONTENT_GAP",
                    "url": rep_url,
                    "scope": rep_url,
                    "affected_urls": [u for u, _, _ in unrendered_pages],
                    "impact": "Non-JavaScript AI retrieval engines (SearchGPT, PerplexityBot) ingest an empty shell without product listings or catalog prose.",
                    "evidence": f"Initial HTML on {rep_url} contains only {rep_words} words before JavaScript execution across {len(unrendered_pages)} route(s).",
                    "suggested_action": {
                        "summary": f"Enable server-side rendering or edge pre-rendering for {rep_url}.",
                        "technical_fix": "Implement edge pre-rendering or SSR to serve hydrated HTML with complete catalog listings to search bots.",
                        "creative_fix": "Provide descriptive static fallback copy in <noscript> or static HTML blocks for crawler indexing.",
                        "priority": "high",
                        "verification": f"Fetch raw HTML of {rep_url} without JavaScript and verify catalog text is present.",
                    },
                }
            )

    # Rule HF-05: Restrictive Snippet Controls on Core Content (nosnippet / max-snippet:0 / data-nosnippet)
    all_pages = inv.get("pages", []) if inv else [{"url": base + "/", "html": html}]
    for page in all_pages:
        p_html = page.get("html", "")
        p_url = page.get("url", base)
        if p_html:
            has_nosnippet = bool(re.search(r"<meta[^>]+content=[^>]*\bnosnippet\b", p_html, re.IGNORECASE))
            has_zero_snippet = bool(re.search(r"<meta[^>]+content=[^>]*max-snippet\s*:\s*0\b", p_html, re.IGNORECASE))
            data_nosnippet_matches = len(re.findall(r"\bdata-nosnippet\b", p_html, re.IGNORECASE))

            if has_nosnippet or has_zero_snippet:
                directive = "nosnippet" if has_nosnippet else "max-snippet:0"
                findings.append(
                    {
                        "category": "crawlability",
                        "title": f"Snippet suppression directive active on core page ({directive}) (HF-05)",
                        "severity": "high",
                        "confidence": "high",
                        "root_cause": f"Page {p_url} declares '{directive}' directive. Under Google AI Overviews, SearchGPT, and Perplexity indexing rules, snippet suppression prevents models from displaying quotes, definitions, or verified facts in synthesized answers.",
                        "cause_family": "CRAWLER.ACCESS_DENIED",
                        "id": "NOSNIPPET_ON_CORE_CONTENT",
                        "cause_id": "NOSNIPPET_ON_CORE_CONTENT",
                        "evidence": f"Found '{directive}' directive in HTML metadata on {p_url}.",
                        "impact": "Generative search engines cannot display or quote textual snippets from this page in synthesized answers.",
                        "suggested_action": {
                            "summary": f"Remove {directive} directive from indexable informational pages.",
                            "technical_fix": "Replace nosnippet or max-snippet:0 with fine-grained max-snippet:-1 to allow full generative synthesis.",
                            "creative_fix": "Use targeted data-nosnippet only on sensitive or proprietary UI components, not main article or commercial copy.",
                            "priority": "high",
                            "verification": "Confirm nosnippet / max-snippet:0 meta tag is removed from document head.",
                        },
                    }
                )
                break
            elif data_nosnippet_matches >= 3:
                findings.append(
                    {
                        "category": "crawlability",
                        "title": f"Excessive data-nosnippet attributes masking body copy ({data_nosnippet_matches} elements)",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": f"Page {p_url} wraps {data_nosnippet_matches} DOM elements in data-nosnippet attributes, hiding substantive paragraphs from AI search indexers.",
                        "cause_family": "DISCOVERY.REPRESENTATION_AVAILABILITY",
                        "id": "DATA_NOSNIPPET_OVERUSE",
                        "cause_id": "NOSNIPPET_ON_CORE_CONTENT",
                        "evidence": f"Detected {data_nosnippet_matches} data-nosnippet attributes on content elements within {p_url}.",
                        "impact": "AI crawlers treat content inside data-nosnippet as non-quotable, reducing citation probability in generative answers.",
                        "suggested_action": {
                            "summary": "Audit and remove data-nosnippet from product specifications and informational copy.",
                            "technical_fix": "Remove data-nosnippet attribute from semantic <div>, <section>, and <span> tags carrying public product facts.",
                            "creative_fix": "Ensure all core brand claims and feature descriptions remain visible to retrieval parsers.",
                            "priority": "medium",
                            "verification": "Inspect HTML source to confirm data-nosnippet is only applied to internal administrative notes or legal disclaimers.",
                        },
                    }
                )
                break

    # 3. robots.txt Analysis
    # RFC 9309 Rule CR04: File Size Cap (500 KiB / 512,000 octets)
    robots_bytes = len(robots_txt.encode("utf-8")) if robots_txt else 0
    if robots_bytes > 512000:
        findings.append(
            {
                "category": "discoverability",
                "title": "robots.txt exceeds RFC 9309 500 KiB cap (directives truncated)",
                "severity": "medium",
                "confidence": "high",
                "root_cause": f"RFC 9309 section 2.2 stipulates that crawlers parse at least 500 KiB (512,000 octets). This file is {robots_bytes} octets. Directives beyond 500 KiB are discarded by AI retrieval crawlers.",
                "cause_family": "CRAWLER.ACCESS_DENIED",
                "id": "ROBOTS_TXT_OVERSIZED",
                "cause_id": "ROBOTS_TXT_OVERSIZED",
                "impact": "Directives placed after the 500 KiB threshold are ignored, leading to crawler misalignment.",
                "evidence": f"robots.txt size is {robots_bytes} bytes (limit: 512,000 bytes).",
                "suggested_action": {
                    "summary": "Truncate or optimize robots.txt to remain strictly under 500 KiB.",
                    "technical_fix": "Remove redundant Disallow rules, wildcard bloat, or paginate URL-specific blocks into sitemaps.",
                    "creative_fix": "Maintain a clean, minimal robots.txt with top-level section directives.",
                    "priority": "medium",
                    "verification": "Confirm robots.txt byte count is <= 512,000 bytes.",
                },
            }
        )

    # RFC 9309 Rule CR05: Server Error 5xx Fail-Closed State
    if r_status is not None and 500 <= r_status <= 599:
        findings.append(
            {
                "category": "discoverability",
                "title": "robots.txt returns HTTP 5xx server error (RFC 9309 fail-closed)",
                "severity": "critical",
                "confidence": "high",
                "root_cause": f"robots.txt returned HTTP {r_status}. Under RFC 9309 section 2.3.1.2, 5xx server errors cause crawlers to assume a full temporary disallow (fail-closed), halting all indexing.",
                "cause_family": "CRAWLER.ACCESS_DENIED",
                "id": "ROBOTS_5XX_FAIL_CLOSED",
                "cause_id": "ROBOTS_5XX_FAIL_CLOSED",
                "impact": "AI retrieval crawlers suspend all crawling and indexing of the domain until 5xx errors resolve.",
                "evidence": f"GET {base}/robots.txt returned HTTP {r_status}.",
                "suggested_action": {
                    "summary": "Fix web server configuration to return HTTP 200 (or HTTP 404) for robots.txt.",
                    "technical_fix": "Investigate upstream web server, gateway, or CDN configuration returning 5xx.",
                    "creative_fix": "Serve a static robots.txt directly from CDN edge caching.",
                    "priority": "critical",
                    "verification": "Confirm curl -I https://example.com/robots.txt returns HTTP 200.",
                },
            }
        )

    search_bots_total = len([b for b in AI_BOTS if CRAWLER_SEMANTICS.get(b, {}).get("role") == "retrieval"])
    search_bots_allowed = 0 if (r_status is not None and 500 <= r_status <= 599) else search_bots_total

    if r_status == 200 and robots_txt:
        groups, _sitemaps = parse_robots(robots_txt)
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
                    observations.append(
                        {
                            "observation": f"User-initiated fetch bot '{bot}' is disallowed in robots.txt (rule: Disallow: {rule or '/'}).",
                            "impact": sem["impact_desc"],
                            "role": role,
                        }
                    )

        # Disaggregation Architecture: AI Search Crawlers vs. AI Training Harvesters
        search_bots_total = len([b for b in AI_BOTS if CRAWLER_SEMANTICS.get(b, {}).get("role") == "retrieval"])
        search_bots_allowed = search_bots_total - len(blocked_retrieval)
        ai_search_readiness = round((search_bots_allowed / max(search_bots_total, 1)) * 100.0, 1)

        observations.append(
            {
                "observation": f"AI Search Retrieval Readiness is {ai_search_readiness}% ({search_bots_allowed}/{search_bots_total} search indexers permitted).",
                "role": "crawler_disaggregation",
                "impact": "Search crawlers (OAI-SearchBot, Claude-SearchBot, PerplexityBot) determine generative search answer inclusion. Blocking training bots (GPTBot, ClaudeBot) protects proprietary data without reducing AI search citations.",
            }
        )

        # Disallowed retrieval crawlers -> Critical finding
        if blocked_retrieval:
            names = [b[0] for b in blocked_retrieval]
            rules_str = ", ".join(f"{b[0]} (Disallow: {b[2] or '/'})" for b in blocked_retrieval)
            findings.append(
                {
                    "category": "crawlability",
                    "title": f"AI search retrieval crawlers blocked in robots.txt ({', '.join(names)})",
                    "severity": "critical",
                    "confidence": "high",
                    "root_cause": "robots.txt explicitly disallows AI search retrieval crawlers responsible for live citations.",
                    "cause_family": "DISCOVERY.ACCESS",
                    "id": "AI_RETRIEVAL_BLOCKED",
                    "cause_id": "AI_RETRIEVAL_BLOCKED",
                    "impact": "The site is excluded from real-time web grounding and citation generation in ChatGPT Search, Claude, and Perplexity.",
                    "evidence": f"robots.txt disallows {len(blocked_retrieval)} retrieval crawler(s): {rules_str}.",
                    "suggested_action": {
                        "summary": f"Allow AI search retrieval bots ({', '.join(names)}) on public routes in robots.txt.",
                        "technical_fix": "Add 'User-agent: <bot>\\nAllow: /' blocks in robots.txt for all search retrieval bots.",
                        "creative_fix": "Separate AI search retrieval bots from training harvesters to protect IP while preserving visibility.",
                        "priority": "critical",
                        "verification": "Re-fetch robots.txt and verify Allow: / is declared for retrieval crawlers.",
                    },
                }
            )

        # Disallowed training crawlers -> Informational observation
        if blocked_training:
            names = [b[0] for b in blocked_training]
            rules_str = ", ".join(f"{b[0]} (Disallow: {b[2] or '/'})" for b in blocked_training)
            observations.append(
                {
                    "observation": f"Site opts out of AI foundation model training for {len(blocked_training)} crawler(s): {', '.join(names)} ({rules_str}).",
                    "impact": "Content is excluded from foundation model pre-training datasets. (This is an intentional governance opt-out, not an AI search retrieval defect).",
                    "role": "training",
                }
            )

        # Check for selective path disallows targeting search retrieval bots
        for bot in AI_BOTS:
            sem = CRAWLER_SEMANTICS.get(bot, {"role": "general", "impact_desc": ""})
            if sem.get("role") != "retrieval":
                continue
            disallowed_sections = []
            for g in groups:
                agents = [a.lower() for a in g.get("agents", [])]
                if bot.lower() in agents:
                    for k, v in g.get("rules", []):
                        if k == "disallow" and v and v != "":
                            disallowed_sections.append(v)
            if disallowed_sections and not any(bot == b[0] for b in blocked_retrieval):
                findings.append(
                    {
                        "category": "crawlability",
                        "title": f"AI search crawler '{bot}' selectively restricted in robots.txt",
                        "severity": "medium",
                        "confidence": "high",
                        "root_cause": f"robots.txt disallows AI search retrieval crawler '{bot}' from specific content paths ({', '.join(disallowed_sections)}).",
                        "cause_family": "CRAWLER.ACCESS_DENIED",
                        "id": "AI_RETRIEVAL_BLOCKED",
                        "cause_id": "AI_RETRIEVAL_BLOCKED",
                        "impact": f"Search assistant '{sem['platform']}' is blocked from indexing or grounding answers using content under {', '.join(disallowed_sections)}.",
                        "evidence": f"robots.txt declares: User-agent: {bot} -> Disallow: {', '.join(disallowed_sections)}.",
                        "suggested_action": {
                            "summary": f"Review robots.txt disallow rules for {bot}.",
                            "technical_fix": f"Remove disallow rules for public content routes under 'User-agent: {bot}' in robots.txt.",
                            "creative_fix": "Ensure high-value editorial and educational content is accessible to AI search engines.",
                            "priority": "medium",
                            "verification": f"Verify {bot} is permitted to crawl {disallowed_sections[0]} in robots.txt.",
                        },
                    }
                )

    # 4. Proactive /llms.txt and /llms-full.txt content manifest discovery
    llms_present = False
    llms_full_present = False
    if inv is not None:
        llms_info = inv.get("infrastructure", {}).get("llms_txt")
        if llms_info:
            llms_present = llms_info.get("present", False)
        llms_full_info = inv.get("infrastructure", {}).get("llms_full_txt")
        if llms_full_info:
            llms_full_present = llms_full_info.get("present", False)
    else:
        status, l_body, _, _ = safe_fetch(f"{base}/llms.txt", timeout=5, max_bytes=512 * 1024)
        llms_present = status == 200 and bool(l_body)
        f_status, f_body, _, _ = safe_fetch(f"{base}/llms-full.txt", timeout=5, max_bytes=1024 * 1024)
        llms_full_present = f_status == 200 and bool(f_body)

    if llms_present:
        observations.append(
            {
                "observation": "Found valid /llms.txt content manifest.",
                "impact": "Clean markdown manifest facilitates direct LLM agent ingestion.",
                "role": "discovery",
            }
        )
        if not llms_full_present:
            recommendations.append(
                {
                    "id": "PROACTIVE.DISCOVERY.LLMS_FULL_TXT.001",
                    "title": "Publish an /llms-full.txt comprehensive document for AI agents",
                    "category": "discoverability",
                    "summary": "The site publishes /llms.txt but lacks an /llms-full.txt comprehensive file. Under the llmstxt.org standard, /llms-full.txt concatenates complete documentation and product context into a single file, enabling zero-roundtrip agent ingestion without traversing individual links.",
                    "priority": "low",
                    "technical_fix": "Generate and serve /llms-full.txt compiling full markdown documentation for core features and commercial offerings.",
                    "creative_fix": "Include executive summaries and full specifications for each major section in /llms-full.txt.",
                    "verification": f"Verify {base}/llms-full.txt returns HTTP 200 with complete markdown text.",
                }
            )
    else:
        recommendations.append(
            {
                "id": "PROACTIVE.DISCOVERY.LLMS_TXT.001",
                "title": "Publish an /llms.txt and /llms-full.txt markdown index for AI agents",
                "category": "discoverability",
                "summary": "The website does not publish an /llms.txt file. Modern generative search systems (ChatGPT, Perplexity, Claude) and agentic web workers prioritize /llms.txt to ingest clean, hierarchical markdown summaries without HTML parsing overhead.",
                "priority": "low",
                "technical_fix": "Publish an /llms.txt file at the root of the domain linking to key markdown documentation and product pages, accompanied by /llms-full.txt.",
                "creative_fix": "Write clear 1-line descriptions for each section in /llms.txt explaining the primary problem it solves.",
                "verification": f"Verify {base}/llms.txt returns HTTP 200 with text/plain or text/markdown content.",
            }
        )

    # 5. Semantic Landmarks Audit for AI Agent Scrapers
    has_semantic_landmarks = dom.has_main or dom.has_article
    if not has_semantic_landmarks and visible_words > 100:
        recommendations.append(
            {
                "id": "PROACTIVE.DISCOVERY.SEMANTIC_LANDMARKS.001",
                "title": "Adopt semantic HTML tags (<main>, <article>) for AI scraper clarity",
                "category": "discoverability",
                "summary": "The page structure relies on generic <div> containers without semantic <main> or <article> landmark elements. AI scrapers (Readability, Trafilatura, Crawl4AI) rely on HTML5 semantic landmarks to cleanly isolate primary content from navigation chrome, headers, and footers.",
                "priority": "low",
                "technical_fix": "Wrap primary content inside a semantic <main> element and distinct articles or blog posts inside <article> tags.",
                "creative_fix": "Structure page content with clear <header>, <main>, and <aside> regions.",
                "verification": "Inspect DOM to confirm <main> and <article> tags enclose substantive content.",
            }
        )

    # Compute AI Agent Scrapeability Score (0-100)
    raw_html_len = len(html) if html else 0
    clean_text_len = len(" ".join(dom.text))
    snr = round(clean_text_len / max(raw_html_len, 1), 4)

    # Component weights:
    # 1. Retrieval bots allowed: 30 pts
    retrieval_pts = 30.0 * (search_bots_allowed / max(search_bots_total, 1))
    # 2. Raw HTML content available (not empty SPA shell): 25 pts
    raw_content_pts = 25.0 if (visible_words >= 60 and not (dom.spa_root and visible_words < 50)) else 5.0
    # 3. LLM manifests (llms.txt: 12 pts, llms-full.txt: 8 pts): 20 pts
    manifest_pts = (12.0 if llms_present else 0.0) + (8.0 if llms_full_present else 0.0)
    # 4. Semantic landmarks (<main>/<article>): 15 pts
    landmark_pts = 15.0 if has_semantic_landmarks else 5.0
    # 5. SNR token efficiency (SNR >= 0.10: 10 pts, >= 0.05: 5 pts): 10 pts
    snr_pts = 10.0 if snr >= 0.10 else (5.0 if snr >= 0.05 else 2.0)

    ai_agent_scrapeability_score = round(retrieval_pts + raw_content_pts + manifest_pts + landmark_pts + snr_pts, 1)

    ai_agent_scrapeability_summary = {
        "overall_scrapeability_score": ai_agent_scrapeability_score,
        "llms_txt_present": llms_present,
        "llms_full_txt_present": llms_full_present,
        "retrieval_bots_allowed": search_bots_allowed,
        "retrieval_bots_total": search_bots_total,
        "retrieval_bots_allowed_ratio": round(search_bots_allowed / max(search_bots_total, 1), 3),
        "raw_html_content_available": visible_words >= 60,
        "semantic_landmarks_present": has_semantic_landmarks,
        "signal_to_noise_ratio": snr,
    }

    if state_file:
        import tempfile as _tf

        _fd, _tmp = _tf.mkstemp(dir=os.path.dirname(os.path.abspath(state_file)))
        with os.fdopen(_fd, "w") as f:
            json.dump(state, f)
        os.replace(_tmp, state_file)

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "ai_agent_scrapeability_summary": ai_agent_scrapeability_summary,
        "coverage": {
            "visible_words_initial_html": visible_words,
            "robots_txt_status": r_status,
            "canonical_declared": dom.canonical,
            "meta_robots_declared": dom.meta_robots,
            # Counts for continuous orchestrator scoring
            "retrieval_bots_allowed": search_bots_allowed,
            "retrieval_bots_total": search_bots_total,
            "noindex_pages": sum(
                1 for p in all_pages
                if "noindex" in str(p.get("html", "")).lower()[:2000]
                and "<meta" in str(p.get("html", "")).lower()[:2000]
            ),
            "canonical_mismatch_pages": sum(
                1 for p in all_pages
                if p.get("canonical") and domain not in str(p.get("canonical", ""))
            ),
            "total_pages_checked": len(all_pages),
        },
        "limitations": [
            "Raw HTML extractability was evaluated directly; JavaScript headless rendering was not executed."
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Discoverability & Crawler Access Diagnostic Sensor.\n"
            "Deterministically evaluates 37 research checks across RFC 9309 crawler matrices "
            "(16 AI retrieval & training bots), HTTP response headers, meta robots directives, "
            "canonical loops, XML sitemaps, and raw unrendered HTML extractability thresholds (< 25 words)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. https://example.com)")
    parser.add_argument("--inventory", help="Path to pre-crawled site inventory JSON (inv.json) for offline execution")
    parser.add_argument("--state", help="Path to global state JSON (optional multi-turn evaluation)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output serialization format (default: json)")
    args = parser.parse_args()
    base, domain = parse_domain(args.site)
    inv = None
    if args.inventory:
        if os.path.exists(args.inventory):
            try:
                with open(args.inventory, "r", encoding="utf-8") as f:
                    inv = json.load(f)
            except Exception as e:
                inv = {"pages": [], "error": f"Failed to parse inventory: {e}", "status": "inconclusive"}
        else:
            inv = {"pages": [], "error": "Inventory file not found", "status": "inconclusive"}
    res = audit(base, domain, inv=inv, state_file=args.state)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
