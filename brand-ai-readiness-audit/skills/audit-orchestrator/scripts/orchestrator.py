#!/usr/bin/env python3
"""
orchestrator.py - Entrypoint CLI for Brand AI-Readiness Audit Marketplace.
Composes the marketplace's specialist audit skills under a strict global
monotonic deadline (< 5 minutes), enforces the Intent -> Entity -> Fact -> Page
abstraction, deduplicates overlapping signals, groups findings under a pure
causal taxonomy, and emits a strictly validated JSON audit report.

Enforces strict Resource-Type / Content-Type invariants:
  - Non-HTML resources (XML sitemaps, feeds, robots.txt, JSON, PDFs) are handled as
    infrastructure resources and NEVER enter page-level semantic or engagement audits.
  - Supports --format json for machine-readable output.
"""

import sys
import os
import re
import json
import time
import argparse
import tempfile
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
VALIDATOR = os.path.join(SCRIPT_DIR, "validate_report.py")

from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

NON_HTML_EXTENSIONS = (
    ".xml", ".xml.gz", ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif",
    ".svg", ".webp", ".mp4", ".mp3", ".json", ".js", ".css", ".zip",
    ".gz", ".tar", ".ico", ".woff", ".woff2", ".ttf", ".eot"
)


PRIORITY_KEYWORDS = [
    ("product", ["/product/", "/products/", "/p/", "/item/", "/store/", "/shop/"]),
    ("pricing", ["/pricing", "/prices", "/plans", "/billing", "/subscription"]),
    ("service", ["/service", "/services", "/solution", "/solutions", "/offering"]),
    ("category", ["/category/", "/categories/", "/collection/", "/collections/", "/browse/"]),
    ("contact", ["/contact", "/support", "/help", "/reach-us"]),
    ("location", ["/location", "/locations", "/store-locator", "/where-to-buy"]),
    ("about", ["/about", "/company", "/our-team", "/story", "/mission"]),
    ("documentation", ["/docs", "/documentation", "/guide", "/api", "/developer"]),
    ("article", ["/blog/", "/news/", "/article/", "/posts/", "/insights/"]),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit a website for AI discoverability, content extractability, and visitor engagement."
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. example.com or https://example.com)")
    parser.add_argument("--output", "-o", help="Path to save the generated JSON report (defaults to stdout)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format: json (default, machine-readable) or markdown")
    
    # Proactive recommendations flag pair
    parser.add_argument("--include-proactive", dest="include_proactive", action="store_true", default=True,
                        help="Include proactive (non-defect) improvement recommendations (default: True)")
    parser.add_argument("--no-proactive", dest="include_proactive", action="store_false",
                        help="Disable proactive improvement recommendations")

    # Optional assistant representation flags
    parser.add_argument("--with-representation", action="store_true", default=False,
                        help="Run optional assistant-representation-audit skill to cross-check observed AI assistant answers")
    parser.add_argument("--responses", "--observations", dest="responses_file",
                        help="Path to JSON file containing observed AI assistant outputs")

    # Global time limit
    parser.add_argument("--timeout-seconds", type=int, default=300,
                        help="Maximum total audit wall-clock runtime in seconds (default: 300s)")

    # SQLite persistence
    parser.add_argument("--db", help="Path to SQLite database to record audit history (optional)")

    return parser.parse_args()



def normalize_target(site_input):
    """Normalize user input to clean domain and base URL."""
    target = site_input.strip()
    if not (target.startswith("http://") or target.startswith("https://")):
        domain = target.split("/")[0]
        base_url = f"https://{domain}"
    else:
        parts = target.split("://", 1)[1]
        domain = parts.split("/")[0]
        base_url = f"{target.split('://')[0]}://{domain}"
    return domain, base_url


def is_html_response(headers, body_snippet=""):
    """Strict Content-Type verification to ensure only genuine HTML enters page audits."""
    ctype = ""
    for k, v in (headers or {}).items():
        if k.lower() == "content-type":
            ctype = str(v).lower()
            break

    if "text/html" in ctype or "application/xhtml+xml" in ctype:
        return True
    if any(x in ctype for x in ("application/xml", "text/xml", "application/json", "application/pdf", "image/")):
        return False

    # Fallback to inspecting initial snippet if header is ambiguous
    snippet = body_snippet.strip()[:200].lower()
    if snippet.startswith("<?xml") or "<urlset" in snippet or "<sitemapindex" in snippet:
        return False
    if "<!doctype html" in snippet or "<html" in snippet:
        return True

    return False


def is_sitemap_or_non_html_url(url):
    """Early filter to reject sitemaps and non-HTML assets from candidate page lists."""
    u_lower = url.lower().split("?")[0].split("#")[0]
    if u_lower.endswith(NON_HTML_EXTENSIONS):
        return True
    if "sitemap" in u_lower or "feed.xml" in u_lower or "rss.xml" in u_lower or "robots.txt" in u_lower:
        return True
    return False


KNOWN_LOCALES = {"en", "es", "fr", "de", "it", "jp", "ja", "pt", "nl", "zh", "ko", "ru", "ar"}


def extract_locale_and_template(url):
    parsed = urlparse(url)
    segments = [s for s in parsed.path.strip("/").split("/") if s]
    locale = "default"
    if segments and (segments[0].lower() in KNOWN_LOCALES or re.match(r'^[a-z]{2}(-[a-z]{2})?$', segments[0].lower())):
        locale = segments[0].lower()
        logical_path = "/" + "/".join(segments[1:])
    else:
        logical_path = parsed.path or "/"
    return locale, logical_path


def classify_page(url, title=""):
    """Classify an HTML page with confidence, granular page types, and template identification."""
    parsed = urlparse(url)
    locale, logical_path = extract_locale_and_template(url)
    segments = [s for s in logical_path.strip("/").split("/") if s]
    t_lower = (title or "").lower()

    if not segments or logical_path == "/":
        return "homepage", "high", "/", locale

    last_seg = segments[-1]
    # Check for placeholder/template routes
    if last_seg in ("default", "placeholder", "template", "empty", "sample", "test"):
        return "template", "high", logical_path, locale

    # Check for category / listing vs product detail
    if len(segments) == 1 and segments[0] in ("products", "shop", "catalog", "store", "items"):
        return "product_listing", "high", logical_path, locale

    if len(segments) >= 2 and segments[0] in ("products", "p", "product", "item", "items", "shop", "catalog") and segments[1] not in ("default", "all", "category", "categories"):
        return "product_detail", "high", "/products/*", locale

    if any(s in ("category", "categories", "collection", "collections", "browse") for s in segments):
        return "category", "high", logical_path, locale

    if any(s in ("subscription", "subscribe", "club", "membership") for s in segments):
        return "subscription_flow", "high", "/subscription", locale

    if any(s in ("pricing", "prices", "plans", "billing", "pricing-plans") for s in segments):
        return "pricing", "high", "/pricing", locale

    if any(s in ("contact", "support", "help", "contact-us", "reach-us", "get-in-touch") for s in segments):
        return "contact", "high", "/contact", locale

    if any(s in ("location", "locations", "stores", "store-locator", "where-to-buy", "branches") for s in segments):
        return "location", "high", "/locations", locale

    if any(s in ("about", "about-us", "company", "our-team", "story", "mission", "who-we-are") for s in segments):
        return "about", "high", "/about", locale

    if any(s in ("docs", "documentation", "guide", "guides", "api", "developer", "manual") for s in segments):
        return "documentation", "high", "/docs", locale

    if any(s in ("blog", "news", "article", "articles", "posts", "insights", "journal") for s in segments):
        return "article", "high", "/article", locale

    # Title-based inferences with multilingual awareness
    if re.search(r'\b(contact\s*(us|ez-nous)?|contáctenos|kontakt|お問い合わせ)\b', t_lower):
        return "contact", "high", "/contact", locale
    if re.search(r'\b(pricing|plans|tarifs|preise)\b', t_lower):
        return "pricing", "medium", "/pricing", locale
    if re.search(r'\b(subscription|abonnement|suscripción|subscribe)\b', t_lower):
        return "subscription_flow", "high", "/subscription", locale
    if re.search(r'\b(products?|catalog|shop|boutique|tienda)\b', t_lower):
        return "product_listing", "medium", "/products", locale
    if re.search(r'\b(about\s*(us)?|notre\s*histoire|sobre\s*nosotros|company)\b', t_lower):
        return "about", "medium", "/about", locale

    return "other", "low", logical_path, locale


def _visible_words(html):
    text = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", html or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(text.split())


def _extract_title(html):
    m = re.search(r"<title[^>]*>([^<]{1,300})</title>", html or "", re.I)
    return m.group(1).strip() if m else ""


def _parse_sitemap_xml(sitemap_body):
    """Parse sitemap XML body and return (child_sitemaps, page_urls)."""
    child_sitemaps = []
    page_urls = []
    if not sitemap_body or "<loc>" not in sitemap_body:
        return child_sitemaps, page_urls

    locs = [loc.strip() for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap_body, re.IGNORECASE)]

    if "<sitemapindex" in sitemap_body.lower():
        child_sitemaps = locs
    else:
        page_urls = locs

    return child_sitemaps, page_urls


def build_inventory(base_url, max_pages=28, deadline=None):
    """Type-safe, SSRF-bounded inventory crawl separating infrastructure from HTML pages."""
    start = time.time()
    parsed_base = urlparse(base_url)
    target_netloc = parsed_base.netloc.lower()

    inv = {
        "base_url": base_url,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "infrastructure": {
            "robots": None,
            "sitemaps_discovered": [],
            "sitemaps_processed": 0,
            "urls_extracted": 0,
            "same_origin_urls": 0
        },
        "robots": None,
        "pages": [],
        "limitations": []
    }

    # 1. Fetch Homepage
    status, home_html, home_headers, err = safe_fetch(base_url + "/", timeout=10, max_bytes=2*1024*1024)
    if not home_html or status is None:
        return None, {"homepage_reachable": False, "error": err}

    if is_html_response(home_headers, home_html):
        pt, pconf, ptmpl, ploc = classify_page(base_url + "/", _extract_title(home_html))
        inv["pages"].append({
            "url": base_url + "/",
            "status": status,
            "resource_type": "html",
            "content_type": home_headers.get("content-type", "text/html"),
            "page_type": pt,
            "page_type_confidence": pconf,
            "logical_template": ptmpl,
            "locale": ploc,
            "title": _extract_title(home_html),
            "word_count": _visible_words(home_html),
            "html": home_html,
            "headers": home_headers
        })

    # Check deadline
    if deadline and time.time() >= deadline:
        inv["limitations"].append("Inventory truncated at acquisition deadline.")
        return inv, {
            "homepage_reachable": True,
            "html_pages_sampled": len(inv["pages"]),
            "sitemaps_processed": 0,
            "elapsed_seconds": round(time.time() - start, 1)
        }

    # 2. robots.txt
    r_status, robots_txt, _, _ = safe_fetch(base_url + "/robots.txt", timeout=8, max_bytes=512*1024)
    inv["robots"] = {"status": r_status, "text": robots_txt if r_status == 200 else None}
    inv["infrastructure"]["robots"] = inv["robots"]

    sitemap_candidates = []
    if robots_txt and r_status == 200:
        sitemap_candidates = [l.split(":", 1)[1].strip() for l in robots_txt.splitlines()
                              if l.lower().startswith("sitemap:")][:5]
    if not sitemap_candidates:
        sitemap_candidates = [base_url + "/sitemap.xml"]

    # 3. Process Sitemaps as Infrastructure Resources
    extracted_page_urls = []
    sitemaps_to_process = list(sitemap_candidates)
    processed_sitemaps = set()

    while sitemaps_to_process and len(processed_sitemaps) < 8:
        if deadline and time.time() >= deadline:
            break
        sm_url = sitemaps_to_process.pop(0)
        if sm_url in processed_sitemaps:
            continue
        sm_netloc = urlparse(sm_url).netloc.lower()
        if sm_netloc and sm_netloc != target_netloc:
            continue

        processed_sitemaps.add(sm_url)
        inv["infrastructure"]["sitemaps_discovered"].append(sm_url)

        s_status, s_body, _, _ = safe_fetch(sm_url, timeout=8, max_bytes=2*1024*1024)
        if s_status == 200 and s_body:
            inv["infrastructure"]["sitemaps_processed"] += 1
            child_sms, raw_page_urls = _parse_sitemap_xml(s_body)
            # Add child sitemaps to processing queue
            for c_sm in child_sms:
                if c_sm not in processed_sitemaps and urlparse(c_sm).netloc.lower() == target_netloc:
                    sitemaps_to_process.append(c_sm)
            # Collect valid candidate page URLs
            for pu in raw_page_urls:
                if urlparse(pu).netloc.lower() == target_netloc and not is_sitemap_or_non_html_url(pu):
                    extracted_page_urls.append(pu)

    # Also extract in-HTML links from homepage if sitemap yielded few URLs
    if len(extracted_page_urls) < 10 and home_html:
        for m in re.finditer(r'href=["\'](https?://[^"\']+|/[^"\']+)["\']', home_html, re.I):
            href = m.group(1).split("#")[0].split("?")[0]
            full_u = urljoin(base_url, href)
            if urlparse(full_u).netloc.lower() == target_netloc and not is_sitemap_or_non_html_url(full_u):
                extracted_page_urls.append(full_u)

    inv["infrastructure"]["urls_extracted"] = len(extracted_page_urls)
    unique_page_urls = list(dict.fromkeys(extracted_page_urls))
    inv["infrastructure"]["same_origin_urls"] = len(unique_page_urls)

    # 4. Priority Adaptive Selection across Page Types, Templates, and Locales
    seen_urls = {p["url"].rstrip("/") for p in inv["pages"]}
    by_template = {}
    for u in unique_page_urls:
        u_clean = u.rstrip("/")
        if u_clean in seen_urls or u_clean == base_url.rstrip("/"):
            continue
        ptype, pconf, ptmpl, ploc = classify_page(u)
        by_template.setdefault((ptype, ptmpl), []).append(u)

    priority_types = [
        "product_detail", "product_listing", "subscription_flow", "pricing",
        "category", "about", "contact", "location", "documentation", "article", "other"
    ]
    selected_urls = []
    for pt in priority_types:
        matching_keys = [k for k in by_template.keys() if k[0] == pt]
        for k in matching_keys:
            for u in by_template[k][:3]:
                if len(selected_urls) >= max_pages - 1 or (deadline and time.time() >= deadline):
                    break
                selected_urls.append(u)
            if len(selected_urls) >= max_pages - 1 or (deadline and time.time() >= deadline):
                break
        if len(selected_urls) >= max_pages - 1 or (deadline and time.time() >= deadline):
            break

    # 5. Fetch and Content-Type Gate Sampled Pages (Respecting robots.txt)
    rp = None
    if robots_txt and r_status == 200:
        try:
            import urllib.robotparser
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(robots_txt.splitlines())
        except Exception:
            rp = None

    for u in selected_urls:
        if deadline and time.time() >= deadline:
            inv["limitations"].append("Inventory crawl truncated when acquisition time budget was reached.")
            break
        if rp and not rp.can_fetch(DEFAULT_USER_AGENT, u):
            continue  # Respect robots.txt Disallow on crawler fetches

        p_status, p_html, p_headers, _ = safe_fetch(u, timeout=8, max_bytes=2*1024*1024)
        if p_html and is_html_response(p_headers, p_html):
            seen_urls.add(u.rstrip("/"))
            pt, pconf, ptmpl, ploc = classify_page(u, _extract_title(p_html))
            inv["pages"].append({
                "url": u,
                "status": p_status,
                "resource_type": "html",
                "content_type": p_headers.get("content-type", "text/html"),
                "page_type": pt,
                "page_type_confidence": pconf,
                "logical_template": ptmpl,
                "locale": ploc,
                "title": _extract_title(p_html),
                "word_count": _visible_words(p_html),
                "html": p_html,
                "headers": p_headers
            })

    inv["elapsed_seconds"] = round(time.time() - start, 1)


    stats = {
        "homepage_reachable": True,
        "html_pages_sampled": len(inv["pages"]),
        "sitemaps_found": len(inv["infrastructure"]["sitemaps_discovered"]),
        "sitemaps_processed": inv["infrastructure"]["sitemaps_processed"],
        "urls_discovered": inv["infrastructure"]["urls_extracted"],
        "same_origin_urls": inv["infrastructure"]["same_origin_urls"],
        "elapsed_seconds": inv["elapsed_seconds"],
        "page_types": {t: sum(1 for p in inv["pages"] if p.get("page_type") == t)
                       for t in {p.get("page_type") for p in inv["pages"] if p.get("page_type")}}
    }
    return inv, stats


def write_inventory_file(inv):
    try:
        fd, path = tempfile.mkstemp(suffix="_inventory.json", prefix="brand_audit_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(inv, f)
        return path
    except Exception:
        return None


def find_specialist_script(skill_name, script_filename):
    """Dynamically discover a specialist script across known skill directory roots."""
    search_roots = [
        os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", skill_name, "scripts")),
        os.path.abspath(os.path.join(os.getcwd(), "brand-ai-readiness-audit", "skills", skill_name, "scripts")),
        os.path.abspath(os.path.join(os.getcwd(), ".agents", "skills", skill_name, "scripts")),
        os.path.abspath(os.path.join(os.getcwd(), "skills", skill_name, "scripts")),
    ]
    for root in search_roots:
        candidate = os.path.join(root, script_filename)
        if os.path.exists(candidate):
            return candidate
    return None


def run_specialist_tool(script_path, timeout_sec, *args):
    """Execute a specialist script with a dedicated time budget."""
    if not script_path or not os.path.exists(script_path):
        return "not_run", [], [], "specialist script not found", [], {}, []
    try:
        cmd = [sys.executable, script_path] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if proc.returncode != 0:
            err = (proc.stderr or "non-zero exit").strip().splitlines()
            return "failed", [], [], err[-1] if err else "non-zero exit", [], {}, []
        if not proc.stdout.strip():
            return "failed", [], [], "no output produced", [], {}, []
        data = json.loads(proc.stdout)
        if isinstance(data, list):
            return "ok", data, [], None, [], {}, []
        if isinstance(data, dict):
            findings = data.get("findings", [])
            recs = data.get("recommendations", [])
            if not isinstance(findings, list) or not isinstance(recs, list):
                return "failed", [], [], "unrecognized output format", [], {}, []
            observations = data.get("observations", [])
            coverage = data.get("coverage", {})
            limitations = data.get("limitations", [])
            if not isinstance(observations, list):
                observations = []
            if not isinstance(coverage, dict):
                coverage = {}
            if not isinstance(limitations, list):
                limitations = []
            sp_status = str(data.get("status", "ok")).lower()
            if sp_status in ("ok", "success"):
                return "ok", findings, recs, None, observations, coverage, limitations
            if sp_status == "inconclusive":
                return "inconclusive", [], [], data.get("error", "specialist could not gather evidence"), observations, coverage, limitations
            return "failed", [], [], data.get("error", f"specialist reported status '{sp_status}'"), observations, coverage, limitations
    except subprocess.TimeoutExpired:
        return "failed", [], [], f"timed out after {timeout_sec}s", [], {}, []
    except Exception as e:
        return "failed", [], [], str(e), [], {}, []


def proactive_checks(domain, base_url, inv_stats=None):
    recommendations = []
    # If sitemaps were already discovered on the site, do not flag a false 404
    if inv_stats and inv_stats.get("sitemaps_found", 0) > 0:
        return recommendations

    sitemap_status = safe_check_status(f"{base_url}/sitemap.xml", timeout=5)
    if sitemap_status == 404:
        recommendations.append({
            "title": "Establish an integrated XML sitemap and brand identity profile",
            "category": "discovery",
            "rationale": f"GET {base_url}/sitemap.xml returned HTTP 404.",
            "suggested_action": "Publish a canonical sitemap.xml listing all indexable URLs and declare it in robots.txt alongside Organization structured data."
        })
    return recommendations



def deduplicate_recommendations(rec_list):
    seen = {}
    deduped = []
    for r in rec_list:
        if not isinstance(r, dict):
            continue
        title = r.get("title", "").strip()
        summary = r.get("summary") or r.get("suggested_action") or r.get("rationale") or "Implement proactive site improvement."
        priority = str(r.get("priority", "low")).lower()
        if priority not in ("critical", "high", "medium", "low"):
            priority = "low"
        key = " ".join(title.lower().split())
        if key in seen:
            continue
        item = {
            "title": title,
            "summary": summary,
            "priority": priority
        }
        seen[key] = item
        deduped.append(item)
    return deduped


def compose_audit(site, include_proactive=True, with_representation=False,
                  responses_file=None, timeout_seconds=300, return_internal=False):
    start_time = time.time()
    monotonic_deadline = start_time + timeout_seconds
    domain, base_url = normalize_target(site)
    raw_findings = []
    specialists = {}
    specialist_recommendations = []
    all_observations = []
    all_coverage = {}
    all_limitations = []

    # 1. Acquisition Phase (Type-Safe Shared Inventory) - max 60s
    acquisition_deadline = min(monotonic_deadline, start_time + 60)
    inventory, inv_stats = build_inventory(base_url, deadline=acquisition_deadline)
    inventory_path = write_inventory_file(inventory) if inventory else None

    if inventory_path:
        all_coverage["site_inventory"] = inv_stats
        all_limitations.extend(inventory.get("limitations", []))
    elif inv_stats and not inv_stats.get("homepage_reachable", True):
        all_limitations.append(f"Homepage unreachable ({inv_stats.get('error', 'Network error')}); inventory could not be built.")

    # 2. Parallel / Sequential Specialist Dispatch
    specialist_runs = [
        ("discoverability-audit", "Access, robots.txt & rendering risk", "discoverability_check.py", []),
        ("entity-content-audit", "Entity identity & offer extractability", "entity_content_check.py", []),
        ("fact-consistency-audit", "Fact ledger & cross-page consistency", "fact_consistency_check.py", []),
        ("corroboration-authority-audit", "Declared authority link verification", "corroboration_check.py", []),
        ("engagement-context-audit", "Orientation & journey continuity", "engagement_check.py", []),
    ]

    if with_representation:
        rep_args = []
        if responses_file and os.path.exists(responses_file):
            rep_args = ["--responses", responses_file]
        specialist_runs.append(
            ("assistant-representation-audit", "Observed assistant representation cross-check", "representation_check.py", rep_args)
        )
    else:
        specialists["assistant-representation-audit"] = {
            "label": "Observed assistant representation cross-check",
            "status": "not_run",
            "reason": "Optional representation layer disabled (run with --with-representation to enable)"
        }

    for idx, (skill_name, label, filename, extra_args) in enumerate(specialist_runs):
        now = time.time()
        remaining_time = monotonic_deadline - now
        remaining_specialists = len(specialist_runs) - idx

        if remaining_time <= 5:
            specialists[skill_name] = {
                "label": label,
                "status": "not_run",
                "reason": "Execution skipped: global time budget exhausted"
            }
            all_limitations.append(f"{skill_name}: Skipped due to global execution time limit.")
            continue

        spec_timeout = max(10, min(40, int((remaining_time - 5) / max(1, remaining_specialists))))

        script = find_specialist_script(skill_name, filename)
        args = ["--site", base_url, "--format", "json"]
        if inventory_path:
            args += ["--inventory", inventory_path]
        args += extra_args

        status, findings, recs, error, observations, coverage, limitations = \
            run_specialist_tool(script, spec_timeout, *args)

        specialists[skill_name] = {"label": label, "status": status}
        if error:
            specialists[skill_name]["error"] = error
        if coverage:
            all_coverage[skill_name] = coverage
        all_limitations.extend(f"{skill_name}: {l}" for l in limitations)
        for obs in observations:
            if isinstance(obs, dict) and obs.get("observation"):
                all_observations.append(obs)
        raw_findings.extend(findings)
        specialist_recommendations.extend(recs)

    if inventory_path:
        try:
            os.unlink(inventory_path)
        except OSError:
            pass

    # 3. Proactive Improvement Checks
    all_recommendations = list(specialist_recommendations)
    if include_proactive:
        all_recommendations.extend(proactive_checks(domain, base_url, inv_stats=inv_stats))

    # 4. Multi-Locale Finding Consolidation & Deduplication Gate
    clustered_groups = {}
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        cause_id = item.get("cause_id", "GENERIC")
        base_title = re.sub(r'\s*\([^\)]*\)', '', item.get("title", "")).strip()
        cluster_key = (cause_id, base_title.lower())
        clustered_groups.setdefault(cluster_key, []).append(item)

    consolidated_raw = []
    for cluster_key, group in clustered_groups.items():
        if len(group) == 1:
            item = dict(group[0])
            if "scope" not in item:
                item["scope"] = "site" if any(k in item.get("title", "").lower() for k in ("homepage", "robots.txt", "organization")) else "page"
            consolidated_raw.append(item)
        else:
            first = group[0]
            consolidated = dict(first)
            consolidated["scope"] = "page_group"
            base_title = re.sub(r'\s*\([^\)]*\)', '', first.get("title", "")).strip()
            consolidated["title"] = f"{base_title} (across {len(group)} routes)"
            loc_evidences = [g.get("evidence", "") for g in group if g.get("evidence")]
            consolidated["evidence"] = " | ".join(loc_evidences[:4])
            consolidated_raw.append(consolidated)

    final_findings = []
    seen_fps = set()
    demoted = []

    sorted_raw = sorted(consolidated_raw, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "medium") if isinstance(f, dict) else "medium", 99))

    for item in sorted_raw:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity", "medium")).lower()
        if sev not in SEVERITY_ORDER:
            sev = "medium"
        confidence = str(item.get("confidence", "medium")).lower()
        fp = f"{item.get('category', '')}:{item.get('title', '')}"
        if fp in seen_fps:
            continue
        seen_fps.add(fp)

        evidence = str(item.get("evidence", "")).strip()
        if len(evidence) < 5:
            demoted.append(dict(
                title=item.get("title", "Audit observation"),
                category=item.get("category", "general"),
                summary=f"Specialist noted '{item.get('title', '')}' without citing concrete evidence.",
                priority="low"
            ))
            continue

        if sev in ("critical", "high") and confidence == "low":
            demoted.append(dict(
                title=item.get("title", "Audit observation"),
                category=item.get("category", "general"),
                summary=f"Reported with severity '{sev}' but low confidence; held as suggestion pending verification.",
                priority="low"
            ))
            continue

        action = item.get("suggested_action", {})
        action_summary = action.get("summary") if isinstance(action, dict) else str(action)
        action_priority = action.get("priority", sev if sev != "info" else "low") if isinstance(action, dict) else sev

        finding_entry = {
            "id": f"F-{len(final_findings) + 1:03d}",
            "title": item.get("title", "Audit Finding"),
            "severity": sev,
            "category": item.get("category", "general"),
            "root_cause": item.get("root_cause") or item.get("title", "Underlying architectural root cause."),
            "confidence": confidence,
            "evidence": evidence,
            "suggested_action": {
                "summary": action_summary or "Review and resolve the identified defect.",
                "priority": action_priority
            }
        }

        final_findings.append(finding_entry)

    all_recommendations.extend(demoted)
    deduped_recommendations = deduplicate_recommendations(all_recommendations)

    summary_counts = {
        "total_findings": len(final_findings),
        "critical": sum(1 for f in final_findings if f["severity"] == "critical"),
        "high": sum(1 for f in final_findings if f["severity"] == "high"),
        "medium": sum(1 for f in final_findings if f["severity"] == "medium"),
        "low": sum(1 for f in final_findings if f["severity"] == "low")
    }

    report = {
        "site": domain,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary_counts,
        "findings": final_findings,
        "proactive_actions": deduped_recommendations
    }

    internal_telemetry = {
        "specialists": specialists,
        "audit_metrics": {
            "execution_time_seconds": round(time.time() - start_time, 1),
            "html_pages_sampled": inv_stats.get("html_pages_sampled", 1) if inv_stats else 1,
            "sitemaps_processed": inv_stats.get("sitemaps_processed", 0) if inv_stats else 0,
            "urls_discovered": inv_stats.get("urls_discovered", 0) if inv_stats else 0,
            "page_types_covered": inv_stats.get("page_types", {}) if inv_stats else {},
            "critical_blockers": summary_counts["critical"]
        },
        "coverage": all_coverage,
        "limitations": all_limitations,
        "observations": all_observations[:100]
    }

    if return_internal:
        return report, internal_telemetry
    return report


def validation_gate(report):
    try:
        proc = subprocess.run(
            [sys.executable, VALIDATOR, "-", "--quiet"],
            input=json.dumps(report), capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0:
            return True
        sys.stderr.write("Validation gate FAILED; report not emitted:\n")
        sys.stderr.write(proc.stderr or "unknown validation error\n")
        return False
    except Exception as e:
        sys.stderr.write(f"Validation gate could not run: {e}\nReport not emitted.\n")
        return False


def format_markdown_report(report):
    lines = []
    site = report.get("site", "Target Site")
    summary = report.get("summary", {})

    lines.append(f"# Brand AI-Readiness Audit Report: {site}")
    lines.append(f"**Audited At:** {report.get('audited_at', 'N/A')}  ")
    lines.append(f"**Total Findings:** {summary.get('total_findings', 0)} (Critical: {summary.get('critical', 0)}, High: {summary.get('high', 0)}, Medium: {summary.get('medium', 0)}, Low: {summary.get('low', 0)})  ")
    lines.append("")

    findings = report.get("findings", [])
    if findings:
        lines.append("## Key Findings")
        for f in findings:
            fid = f.get("id", "F-???")
            sev = f.get("severity", "medium").upper()
            title = f.get("title", "Finding")
            cat = f.get("category", "")
            lines.append(f"### [{sev}] {fid}: {title}")
            if cat:
                lines.append(f"- **Category:** {cat}")
            lines.append(f"- **Root Cause:** {f.get('root_cause', 'N/A')}")
            lines.append(f"- **Confidence:** {f.get('confidence', 'medium')}")
            lines.append(f"- **Evidence:** {f.get('evidence', 'None')}")
            action = f.get("suggested_action", {})
            action_summary = action.get("summary") if isinstance(action, dict) else str(action)
            action_priority = action.get("priority", "medium") if isinstance(action, dict) else "medium"
            lines.append(f"- **Suggested Action:** {action_summary} (Priority: {action_priority})")
            lines.append("")
    else:
        lines.append("## Key Findings")
        lines.append("No critical or high-severity defects detected across audited pages.")
        lines.append("")

    proactive = report.get("proactive_actions", [])
    if proactive:
        lines.append("## Proactive Actions")
        for r in proactive:
            lines.append(f"- **{r.get('title', 'Recommendation')}** (Priority: {r.get('priority', 'low')}): {r.get('summary', '')}")
        lines.append("")

    return "\n".join(lines)


def main():
    args = parse_args()
    report, internal_data = compose_audit(
        args.site,
        include_proactive=args.include_proactive,
        with_representation=args.with_representation,
        responses_file=args.responses_file,
        timeout_seconds=args.timeout_seconds,
        return_internal=True
    )

    if not validation_gate(report):
        sys.exit(1)

    # Save to SQLite if requested
    if args.db:
        try:
            from audit_db import save_audit_report
            save_audit_report(report, internal_data=internal_data, db_path=args.db)
        except Exception as e:
            sys.stderr.write(f"SQLite save warning: {e}\n")

    if args.format == "markdown":
        out_content = format_markdown_report(report)
    else:
        out_content = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_content + "\n")
    else:
        print(out_content)


if __name__ == "__main__":
    main()
