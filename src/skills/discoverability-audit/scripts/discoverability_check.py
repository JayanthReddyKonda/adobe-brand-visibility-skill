#!/usr/bin/env python3
"""
discoverability_check.py - Access & discovery layer of the Brand AI-Readiness Audit.
Provides pure empirical telemetry on RFC 9309 crawler matrices, robots.txt status,
meta tags, canonicals, hreflangs, and raw HTML rendering extractability.
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "web-scraper", "scripts"))
for _p in (SCRIPT_DIR, SCRAPER_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from safe_fetch import safe_fetch  # type: ignore

AI_BOTS = [
    "OAI-SearchBot", "Claude-SearchBot", "anthropic-ai", "PerplexityBot",
    "Amazonbot", "cohere-ai", "Meta-ExternalAgent", "Claude-User",
    "Perplexity-User", "ChatGPT-User", "GPTBot", "ClaudeBot",
    "Bytespider", "Applebot-Extended", "Google-Extended", "CCBot",
]

RETRIEVAL_BOTS = {"OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "anthropic-ai"}

SPA_ID_PATTERNS = re.compile(
    r"^(root|app|mount|__next|__nuxt|app-root|___gatsby|svelte|svelte-app|react-root|vue-app|app-container|main-app|application)$",
    re.IGNORECASE,
)
SPA_CLASS_PATTERNS = re.compile(
    r"\b(react-root|vue-app|app-container|spa-container|application-root|mount-point)\b", re.IGNORECASE
)

_VALID_LANGUAGES = {
    "ab", "aa", "af", "ak", "sq", "am", "ar", "an", "hy", "as", "av", "ae", "ay", "az", "bm", "ba", "eu", "be", "bn",
    "bi", "bs", "br", "bg", "my", "ca", "ch", "ce", "ny", "zh", "cv", "kw", "co", "cr", "hr", "cs", "da", "dv", "nl",
    "dz", "en", "eo", "et", "ee", "fo", "fj", "fi", "fr", "ff", "gl", "ka", "de", "el", "gn", "gu", "ht", "ha", "he",
    "hz", "hi", "ho", "hu", "ia", "id", "ie", "ga", "ig", "ik", "io", "is", "it", "iu", "ja", "jv", "kl", "kn", "kr",
    "ks", "kk", "km", "ki", "rw", "ky", "kv", "kg", "ko", "ku", "kj", "la", "lb", "lg", "li", "ln", "lo", "lt", "lu",
    "lv", "gv", "mk", "mg", "ms", "ml", "mt", "mi", "mr", "mh", "mn", "na", "nv", "nd", "ne", "ng", "nb", "nn", "no",
    "ii", "nr", "oc", "oj", "cu", "om", "or", "os", "pa", "pi", "fa", "pl", "ps", "pt", "qu", "rm", "rn", "ro", "ru",
    "sa", "sc", "sd", "se", "sm", "sg", "sr", "gd", "sn", "si", "sk", "sl", "so", "st", "es", "su", "sw", "ss", "sv",
    "ta", "te", "tg", "th", "ti", "bo", "tk", "tl", "tn", "to", "tr", "ts", "tt", "tw", "ty", "ug", "uk", "ur", "uz",
    "ve", "vi", "vo", "wa", "cy", "wo", "fy", "xh", "yi", "yo", "za", "zu",
}


def is_valid_hreflang(code: str) -> bool:
    """Validate BCP 47 language/region format."""
    normalized = str(code or "").strip()
    if normalized.lower() == "x-default":
        return True
    parts = normalized.split("-")
    if len(parts) == 1:
        return parts[0].lower() in _VALID_LANGUAGES and parts[0].islower()
    if len(parts) == 2:
        lang, reg = parts[0], parts[1]
        valid_lang = lang.lower() in _VALID_LANGUAGES and lang.islower()
        valid_reg = (len(reg) == 2 and reg.isupper() and reg.isalpha()) or (len(reg) == 3 and reg.isdigit())
        return valid_lang and valid_reg
    return False


class Dom(HTMLParser):
    """Streaming HTML parser extracting discoverability signals."""

    def __init__(self):
        super().__init__()
        self.meta_robots = ""
        self.canonical = ""
        self.canonicals: List[str] = []
        self.hreflangs: List[Dict[str, str]] = []
        self.links: List[str] = []
        self.text: List[str] = []
        self.skip = 0
        self.spa_root = False
        self.spa_marker_name = ""

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        a = dict(attrs)
        if t in ("script", "style", "noscript"):
            self.skip += 1
        if t == "link" and (a.get("rel") or "").lower() == "alternate" and a.get("hreflang"):
            self.hreflangs.append({"lang": a.get("hreflang", ""), "href": a.get("href", "")})
        if t == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href", "")
            if self.canonical:
                self.canonicals.append(self.canonical)
        if t == "meta" and (a.get("name") or "").lower() == "robots":
            self.meta_robots = a.get("content", "")

        cid = (a.get("id") or "").strip()
        ccls = (a.get("class") or "").strip()
        if t in ("div", "main", "section"):
            if cid and SPA_ID_PATTERNS.match(cid):
                self.spa_root = True
                self.spa_marker_name = f"<{t} id='{cid}'>"
            elif ccls and SPA_CLASS_PATTERNS.search(ccls):
                self.spa_root = True
                self.spa_marker_name = f"<{t} class='{ccls}'>"
        elif t in ("app-root", "app-main", "ng-component", "router-outlet") or "data-reactroot" in a or "data-v-app" in a:
            self.spa_root = True
            self.spa_marker_name = f"<{t}>"

        if t == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        txt = data.strip()
        if not self.skip and txt:
            self.text.append(txt)


def parse_domain(site: str) -> Tuple[str, str]:
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    return f"{p.scheme}://{p.netloc}", p.netloc


def parse_robots(body: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    groups: List[Dict[str, Any]] = []
    sitemaps: List[str] = []
    if not isinstance(body, str):
        return groups, sitemaps
    current: Optional[Dict[str, Any]] = None
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


def _pattern_matches(pattern: str, path: str) -> bool:
    pat = re.escape(pattern).replace(r"\*", ".*")
    if pat.endswith(r"\$"):
        pat = pat[:-2] + "$"
    return re.match(pat, path) is not None


def robots_access(groups: List[Dict[str, Any]], ua: str, path: str = "/") -> Tuple[str, Optional[str]]:
    ua = ua.lower()
    specific_rules: List[Tuple[str, str]] = []
    wildcard_rules: List[Tuple[str, str]] = []
    for g in groups:
        agents = [a.lower() for a in g.get("agents", [])]
        if ua in agents:
            specific_rules.extend(g.get("rules", []))
        elif "*" in agents:
            wildcard_rules.extend(g.get("rules", []))

    rules = specific_rules if specific_rules else wildcard_rules
    best: Tuple[str, Optional[str], int] = ("allow", None, -1)
    for k, v in rules:
        if not v:
            continue
        if _pattern_matches(v, path):
            spec = len(v)
            if (k == "allow" and spec == best[2]) or spec > best[2]:
                best = (k, v, spec)
    return best[0], best[1]


def check_bot_permission(robots_txt: str, bot: str, path: str = "/") -> Tuple[str, Optional[str]]:
    if not robots_txt:
        return "allow", None
    groups, _ = parse_robots(robots_txt)
    return robots_access(groups, bot, path)


def make_finding(cause_id: str, title: str, severity: str, scope: str, evidence: Any, root_cause: str = "", category: str = "discoverability") -> Dict[str, Any]:
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
        "impact": f"Impairs AI search engine discovery and indexing: {title}",
        "suggested_action": {
            "summary": f"Remediate {cause_id} on {scope}",
            "technical_fix": f"Update web server and robots configuration for {cause_id}.",
            "creative_fix": f"Ensure machine discovery tags align on {scope}.",
            "priority": severity,
            "verification": f"Verify {scope} returns expected headers and status.",
        },
    }


def audit(base: str, domain: str, inv: Optional[Dict[str, Any]] = None, state_file: Optional[str] = None,
          target_url: Optional[str] = None, target_bot: Optional[str] = None, subsystem: Optional[str] = None) -> Dict[str, Any]:
    """Execute discoverability sensor against site or inventory."""
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

    # 1. Fetch or parse robots.txt and entrypoint
    status = 200
    headers: Dict[str, str] = {}
    html = ""
    robots_txt = ""
    robots_status = 200

    if inv:
        pages = inv.get("pages", [])
        if pages:
            hp = next((p for p in pages if p.get("page_type") == "homepage" or p.get("url") in (base, base + "/")), pages[0])
            status = hp.get("status", 200)
            headers = {k.lower(): v for k, v in (hp.get("headers") or {}).items()}
            html = hp.get("html", "") or hp.get("text", "")
        rob_data = inv.get("robots")
        if isinstance(rob_data, dict):
            robots_txt = rob_data.get("raw", "")
            robots_status = rob_data.get("status", 200)
        elif isinstance(rob_data, str):
            robots_txt = rob_data
        if not robots_txt and inv.get("robots_txt"):
            rt_val = inv.get("robots_txt")
            if isinstance(rt_val, str):
                robots_txt = rt_val
    else:
        status, html, headers, _ = safe_fetch(base + "/", timeout=10, max_bytes=2097152) if safe_fetch else (200, "", {}, "")
        rob_st, rob_body, _, _ = safe_fetch(base + "/robots.txt", timeout=8, max_bytes=524288) if safe_fetch else (200, "", {}, "")
        status = status or 200
        html = html or ""
        headers = headers or {}
        robots_txt = rob_body or ""
        robots_status = rob_st or 200

    # 2. Evaluate Root Entrypoint Status
    if status in (403, 401, 500, 502, 503):
        findings.append(make_finding("AI_RETRIEVAL_BLOCKED", f"HTTP status {status} on root URL", "critical", base, f"GET {base}/ returned HTTP {status}."))

    # 3. Robots RFC 9309 crawler matrices
    groups, sitemaps = parse_robots(robots_txt)
    bot_matrix: Dict[str, bool] = {}
    blocked_retrieval_bots: List[str] = []

    for b in AI_BOTS:
        dec, _ = robots_access(groups, b, "/")
        allowed = (dec != "disallow") and (robots_status != 500 and robots_status != 503)
        bot_matrix[b] = allowed
        if not allowed and b in RETRIEVAL_BOTS:
            blocked_retrieval_bots.append(b)

    if blocked_retrieval_bots:
        findings.append(make_finding(
            "AI_RETRIEVAL_BLOCKED",
            f"AI retrieval bots disallowed in robots.txt ({', '.join(blocked_retrieval_bots)})",
            "critical",
            f"{base}/robots.txt",
            f"robots.txt disallows: {', '.join(blocked_retrieval_bots)}",
        ))

    # 4. Parse DOM & Inspect Meta Directives
    dom = Dom()
    try:
        dom.feed(html)
    except Exception:
        pass

    x_robots = str(headers.get("x-robots-tag", "")).lower()
    meta_tag = str(dom.meta_robots or "").lower()
    robot_tokens = {d.strip() for d in re.split(r"[,;\s]+", f"{meta_tag} {x_robots}") if d.strip()}

    if "noindex" in robot_tokens or "none" in robot_tokens:
        findings.append(make_finding("NOINDEX_EXCLUSION", "Homepage explicitly excludes indexers (noindex directive)", "critical", base, f"Direct noindex in meta/headers: {robot_tokens}"))
    if "nosnippet" in robot_tokens:
        findings.append(make_finding("NOSNIPPET_RESTRICTION", "Homepage restricts search snippets (nosnippet directive)", "high", base, "Found nosnippet token in robots meta"))

    # Malformed JSON-LD check
    all_htmls = [html] + [p.get("html", "") or p.get("raw_html", "") for p in (inv.get("pages", []) if inv else [])]
    for h_content in all_htmls:
        if not h_content:
            continue
        scripts = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', h_content, re.DOTALL | re.IGNORECASE)
        for s in scripts:
            s_clean = s.strip()
            if s_clean:
                try:
                    json.loads(s_clean)
                except Exception:
                    findings.append({
                        "id": "E5_MALFORMED_JSONLD",
                        "cause_id": "E5_MALFORMED_JSONLD",
                        "check_id": "E5",
                        "title": "Malformed JSON-LD syntax in HTML",
                        "severity": "high",
                        "category": "entity",
                        "confidence": "high",
                        "scope": base,
                        "evidence": {"summary": "JSON-LD script block contains unparseable syntax errors.", "sources": [{"url": base, "observation": "JSON decode error in application/ld+json block."}]},
                        "root_cause": "Malformed JSON-LD script block prevented search engine entity graph indexing.",
                        "impact": "Search engines and AI agents fail to extract structured entity representations.",
                        "suggested_action": {
                            "summary": "Fix syntax errors in application/ld+json script blocks.",
                            "technical_fix": "Validate JSON-LD syntax with standard validator and ensure all brackets and quotes match.",
                            "creative_fix": "Ensure CMS structured data templates produce valid JSON strings.",
                            "priority": "high",
                            "verification": "Verify application/ld+json blocks pass json.loads() cleanly.",
                        },
                    })
                    break
        if any(f.get("id") == "E5_MALFORMED_JSONLD" for f in findings):
            break

    # Inspect inventory pages for noindex and canonical mismatches
    canonical_mismatches = 0
    pages_list = inv.get("pages", []) if inv else []
    if pages_list:
        sub_noindex: List[str] = []
        for p in pages_list:
            pu = p.get("url") or ""
            p_tokens = {d.strip().lower() for d in (p.get("robots_meta") or []) + (p.get("x_robots_tag") or [])}
            if (p.get("noindex") or "noindex" in p_tokens or "none" in p_tokens) and (pu.rstrip("/") not in (base.rstrip("/"), (base + "/").rstrip("/"))):
                sub_noindex.append(pu)
            p_can = p.get("canonical")
            if p_can and pu and p_can.rstrip("/") != pu.rstrip("/"):
                canonical_mismatches += 1

        if sub_noindex and not any(f["cause_id"] == "NOINDEX_EXCLUSION" for f in findings):
            findings.append(make_finding("NOINDEX_EXCLUSION", "Sub-pages contain noindex directives", "high", base, f"Found noindex on: {', '.join(sub_noindex[:5])}"))
        if canonical_mismatches > 0:
            findings.append(make_finding("CANONICAL_FRAGMENTATION", f"Canonical URL mismatches detected ({canonical_mismatches} pages)", "medium", base, f"{canonical_mismatches} pages have divergent canonical URLs"))

    # 5. CSR / SPA Shell Check
    csr_pages = []
    if len(dom.text) < 25 and dom.spa_root:
        csr_pages.append({"url": base, "page_type": "homepage", "word_count": len(dom.text)})

    for p in pages_list:
        pu = p.get("url") or ""
        p_html = p.get("html") or ""
        p_wc = p.get("word_count")
        if p_wc is None:
            p_text = re.sub(r"<[^>]+>", " ", p_html)
            p_wc = len(re.findall(r"\b\w+\b", p_text))
        has_spa = bool(re.search(r'<(?:div|section)\s+id=["\'](?:root|app|__next|___gatsby)["\']', p_html, re.I))
        if p_wc < 25 and has_spa and not any(cp["url"] == pu for cp in csr_pages):
            csr_pages.append({"url": pu, "page_type": p.get("page_type", "general"), "word_count": p_wc})

    if csr_pages:
        def _route_score(cp):
            u = cp["url"].lower()
            pt = cp.get("page_type", "")
            if pt == "product_detail" or "/products/" in u or "/product/" in u or "/pricing" in u:
                return 3
            if "quiz" in u or "content/dam" in u:
                return 1
            return 2

        csr_pages_sorted = sorted(csr_pages, key=_route_score, reverse=True)
        rep_page = csr_pages_sorted[0]
        rep_url = rep_page["url"]
        rep_ptype = rep_page.get("page_type", "")

        if rep_ptype == "product_detail":
            title = "Primary copy missing from initial raw HTML (client-side rendering gap on product_detail routes)"
        elif rep_ptype in ("core", "pricing", "general") or not rep_ptype:
            title = "Primary copy missing from initial raw HTML (client-side rendering gap on core routes)"
        else:
            title = f"Primary copy missing from initial raw HTML (client-side rendering gap on {rep_ptype} routes)"

        finding = make_finding(
            "RENDERED_CONTENT_GAP",
            title,
            "high",
            rep_url,
            f"Client-side rendering gap detected across {len(csr_pages)} routes; initial HTML contains minimal textual content before JS execution.",
        )
        finding["affected_urls"] = [cp["url"] for cp in csr_pages]
        findings.append(finding)

    # 6. Hreflang Validation
    invalid_langs: List[str] = []
    for hl in dom.hreflangs:
        code = str(hl.get("lang", "")).strip()
        if code and not is_valid_hreflang(code):
            invalid_langs.append(code)
    if invalid_langs:
        findings.append(make_finding("INVALID_HREFLANG", f"Invalid hreflang codes detected ({', '.join(invalid_langs)})", "medium", base, f"Invalid codes: {invalid_langs}"))

    # Recommendations
    if not sitemaps:
        recommendations.append({"id": "REC-DISC-01", "title": "Declare XML Sitemap in robots.txt", "summary": "Add Sitemap directive to robots.txt to accelerate bot discovery.", "priority": "medium"})

    # Filter by subsystem if specified
    if subsystem == "access":
        findings = [f for f in findings if f["cause_id"] in ("AI_RETRIEVAL_BLOCKED", "NOINDEX_EXCLUSION", "NOSNIPPET_RESTRICTION")]
    elif subsystem == "rendering":
        findings = [f for f in findings if f["cause_id"] == "RENDERED_CONTENT_GAP"]
    elif subsystem == "canonical":
        findings = [f for f in findings if f["cause_id"] == "CANONICAL_FRAGMENTATION"]

    word_count = len(dom.text)
    is_csr_shell = bool(csr_pages)

    res: Dict[str, Any] = {
        "status": "ok",
        "telemetry": {
            "entrypoint_status": status,
            "robots_status": robots_status,
            "bot_permissions": bot_matrix,
            "sitemaps": sitemaps,
            "word_count": word_count,
            "is_csr_shell": is_csr_shell,
            "canonical_mismatches": canonical_mismatches,
        },
        "findings": findings,
        "recommendations": recommendations,
    }

    # Custom parameter forensics
    if target_bot:
        dec, rule = robots_access(groups, target_bot, "/")
        res["bot_permission"] = {"bot": target_bot, "decision": dec, "rule": rule, "is_allowed": dec != "disallow"}
    if target_url:
        target_p = next((p for p in (inv.get("pages", []) if inv else []) if p.get("url") == target_url), None)
        wc = target_p.get("word_count", 150) if target_p else 150
        res["target_inspection"] = {"url": target_url, "status": target_p.get("status", 200) if target_p else 200, "word_count": wc}

    return res


def main():
    parser = argparse.ArgumentParser(description="Discoverability Diagnostic Sensor")
    parser.add_argument("--site", "-s", default=None)
    parser.add_argument("--inventory", "-i", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--url", help="Target specific route for forensic inspection")
    parser.add_argument("--bot", help="Test RFC 9309 crawler permissions for specific bot")
    parser.add_argument("--subsystem", choices=["access", "rendering", "render", "canonical", "sitemaps"])
    parser.add_argument("--matrix-only", dest="matrix_only", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    if args.matrix_only:
        args.subsystem = "access"
    elif args.subsystem == "render":
        args.subsystem = "rendering"

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

    base, domain = parse_domain(site_str)
    res = audit(base, domain, inv=inv, state_file=args.state, target_url=args.url, target_bot=args.bot, subsystem=args.subsystem)
    out = json.dumps(res, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
