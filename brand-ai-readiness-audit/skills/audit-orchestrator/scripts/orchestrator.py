#!/usr/bin/env python3
"""
orchestrator.py - Entrypoint CLI for Brand AI-Readiness Audit Marketplace.
Composes the marketplace's specialist audit skills, reconciles their
evidence-backed findings, deduplicates overlapping signals, adds proactive
improvement recommendations, and emits a strictly validated JSON audit report.

Guarantees:
  - All findings derive from real, on-demand checks. Nothing is fabricated.
  - Specialist execution status is always recorded ("ok" / "failed" /
    "not_run"). Tool failure is NEVER converted into zero findings.
  - The final report is validated before being emitted; on validation
    failure the orchestrator exits non-zero instead of emitting.

Usage:
  python3 orchestrator.py --site example.com [--output report.json]
"""

import sys
import os
import re
import json
import argparse
import tempfile
from datetime import datetime, timezone
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(SCRIPT_DIR, "validate_report.py")

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit a website for AI discoverability and on-site engagement by composing specialist skills."
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. example.com or https://example.com)")
    parser.add_argument("--output", "-o", help="Path to save the generated JSON report (defaults to stdout)")
    parser.add_argument("--include-proactive", action="store_true", default=True,
                        help="Include proactive (non-defect) improvement recommendations (default: True)")
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


def find_specialist_script(skill_name, script_filename):
    """Dynamically discover a specialist script across common skill layouts."""
    search_roots = [
        os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", skill_name, "scripts")),
        os.path.abspath(os.path.join(os.getcwd(), "brand-ai-readiness-audit", "skills", skill_name, "scripts")),
        os.path.abspath(os.path.join(os.getcwd(), ".agents", "skills", skill_name, "scripts")),
    ]
    for root in search_roots:
        candidate = os.path.join(root, script_filename)
        if os.path.exists(candidate):
            return candidate
    return None


def run_specialist_tool(script_path, *args):
    """Execute a specialist script. Returns (status, findings, recommendations, error).

    status: "ok" | "failed" | "not_run". A failed or not_run specialist
    contributes NO findings and NO implicit "clean" signal - the status is
    surfaced in the report instead.
    """
    if not script_path or not os.path.exists(script_path):
        return "not_run", [], [], "specialist script not found", [], {}, []
    try:
        cmd = [sys.executable, script_path] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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
            # Unified evidence contract (v3): specialists may also emit
            # observations[], coverage{}, limitations[]. Missing keys are
            # tolerated for backwards compatibility.
            observations = data.get("observations", [])
            coverage = data.get("coverage", {})
            limitations = data.get("limitations", [])
            if not isinstance(observations, list):
                observations = []
            if not isinstance(coverage, dict):
                coverage = {}
            if not isinstance(limitations, list):
                limitations = []
            # Honor the specialist's own self-reported status: an
            # "inconclusive"/"failed" specialist must never be recorded as
            # "ok" with zero findings (that would masquerade as a clean site).
            sp_status = str(data.get("status", "ok")).lower()
            if sp_status in ("ok", "success"):
                return "ok", findings, recs, None, observations, coverage, limitations
            if sp_status == "inconclusive":
                return ("inconclusive", [], [], data.get("error", "specialist could not gather evidence"),
                        observations, coverage, limitations)
            return ("failed", [], [], data.get("error", f"specialist reported status '{sp_status}'"),
                    observations, coverage, limitations)
    except subprocess.TimeoutExpired:
        return "failed", [], [], "timed out after 120s", [], {}, []
    except Exception as e:
        return "failed", [], [], str(e), [], {}, []

def check_url_status(url, timeout=5):
    """GET a URL and return its HTTP status code, or None if unreachable."""
    import urllib.request
    import urllib.error
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def fetch_page(url, timeout=8):
    """GET a URL; return (status, body, headers). Never raises."""
    import urllib.request
    import urllib.error
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"})
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


# --- Shared site inventory -------------------------------------------------
# One bounded acquisition pass shared by ALL specialists: homepage + robots +
# sitemap + priority pages (page-type classified). Specialists receive the
# inventory file and operate on the SAME evidence snapshot; without it they
# fetch for themselves (backwards compatible).

PRIORITY_KEYWORDS = [
    ("product", ["product", "/p/", "shop", "store", "item"]),
    ("pricing", ["pricing", "price", "plans", "billing"]),
    ("service", ["service", "solution", "offering"]),
    ("category", ["category", "collection", "catalog"]),
    ("contact", ["contact", "support", "help"]),
    ("location", ["location", "store-locator", "branch"]),
    ("about", ["about", "company", "team", "story"]),
    ("documentation", ["docs", "documentation", "guide", "api", "developer", "help-center"]),
    ("article", ["blog", "news", "article", "post", "insight"]),
]


def classify_page(url, title=""):
    """Classify a page by URL/title keywords. 'other' is a valid class."""
    hay = (url + " " + (title or "")).lower()
    for ptype, kws in PRIORITY_KEYWORDS:
        if any(k in hay for k in kws):
            return ptype
    return "other"


def _visible_words(html):
    text = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", html or "",
                  flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(text.split())


def _extract_title(html):
    m = re.search(r"<title[^>]*>([^<]{1,300})</title>", html or "", re.I)
    return m.group(1).strip() if m else ""


def _sitemap_urls(sitemap_body, limit=60):
    return [loc.strip() for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>",
                                              sitemap_body or "")][:limit]


def build_inventory(base_url, max_pages=16, budget_seconds=90):
    """Bounded, page-type-aware crawl. Mandatory: homepage, robots.txt,
    sitemap. Then priority URLs within the time budget. Returns
    (inventory_dict_or_None, stats)."""
    import time
    start = time.time()
    inv = {"base_url": base_url,
           "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "robots": None, "sitemap_urls": [], "pages": [], "limitations": []}

    # 1. Homepage (mandatory)
    status, home_html, headers = fetch_page(base_url + "/")
    if not home_html:
        return None, {"homepage_reachable": False}
    inv["pages"].append({"url": base_url + "/", "status": status, "page_type": "homepage",
                         "title": _extract_title(home_html),
                         "word_count": _visible_words(home_html), "html": home_html})

    # 2. robots.txt (mandatory)
    r_status, robots_txt, _ = fetch_page(base_url + "/robots.txt")
    inv["robots"] = {"status": r_status, "text": robots_txt if r_status == 200 else None}
    sitemap_urls = []
    if robots_txt and r_status == 200:
        sitemap_urls = [l.split(":", 1)[1].strip() for l in robots_txt.splitlines()
                        if l.lower().startswith("sitemap:")][:5]

    # 3. Sitemap (mandatory attempt); expand an index sitemap one level
    locs = []
    for sm in sitemap_urls or [base_url + "/sitemap.xml"]:
        s_status, s_body, _ = fetch_page(sm)
        if s_status == 200 and s_body and "<loc>" in s_body:
            inv["sitemap_urls"].append(sm)
            locs.extend(_sitemap_urls(s_body))
            if "<sitemapindex" in s_body:
                for child in _sitemap_urls(s_body)[:3]:
                    c_status, c_body, _ = fetch_page(child)
                    if c_status == 200 and c_body and "<loc>" in c_body:
                        locs.extend(_sitemap_urls(c_body))
    inv["sitemap_url_count"] = len(locs)

    # 4. Priority selection: classify sitemap URLs, prefer high-value types,
    #    respect the time budget (Adobe brief: <5 min typical runtime).
    seen = {p["url"].rstrip("/") for p in inv["pages"]}
    by_type = {}
    for u in locs:
        if u.rstrip("/") in seen or u.rstrip("/") == base_url:
            continue
        by_type.setdefault(classify_page(u), []).append(u)
    priority_order = ["product", "pricing", "service", "category", "contact",
                      "location", "about", "documentation", "article", "other"]
    selected = []
    for t in priority_order:
        for u in by_type.get(t, [])[:4]:
            if len(selected) >= max_pages - 1 or time.time() - start > budget_seconds:
                break
            selected.append(u)
        if len(selected) >= max_pages - 1 or time.time() - start > budget_seconds:
            break
    for u in selected:
        if time.time() - start > budget_seconds:
            inv["limitations"].append("inventory crawl truncated at time budget")
            break
        p_status, p_html, _ = fetch_page(u)
        if p_html:
            seen.add(u.rstrip("/"))
            inv["pages"].append({"url": u, "status": p_status,
                                 "page_type": classify_page(u),
                                 "title": _extract_title(p_html),
                                 "word_count": _visible_words(p_html), "html": p_html})

    inv["elapsed_seconds"] = round(time.time() - start, 1)
    stats = {"homepage_reachable": True, "pages": len(inv["pages"]),
             "sitemap_urls_discovered": len(locs),
             "elapsed_seconds": inv["elapsed_seconds"],
             "page_types": {t: sum(1 for p in inv["pages"] if p["page_type"] == t)
                            for t in {p["page_type"] for p in inv["pages"]}}}
    return inv, stats


def write_inventory_file(inv):
    """Persist the inventory to a temp file; return the path or None."""
    try:
        fd, path = tempfile.mkstemp(suffix="_inventory.json", prefix="brand_audit_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(inv, f)
        return path
    except Exception:
        return None


def proactive_checks(domain, base_url):
    """Proactive (non-defect) improvement recommendations.

    Each is grounded in a real probe. Inconclusive probes (network errors,
    unexpected statuses) produce NO claim rather than a guess.
    """
    recommendations = []

    llms_status = check_url_status(f"{base_url}/llms.txt")
    if llms_status == 404:
        recommendations.append({
            "title": "Add an /llms.txt file to guide AI assistants",
            "rationale": f"GET {base_url}/llms.txt returned HTTP 404. An llms.txt file gives AI assistants a curated map of key content.",
            "suggested_action": "Publish /llms.txt listing canonical URLs and short descriptions of key pages."
        })

    sitemap_status = check_url_status(f"{base_url}/sitemap.xml")
    if sitemap_status == 404:
        recommendations.append({
            "title": "Add an XML sitemap",
            "rationale": f"GET {base_url}/sitemap.xml returned HTTP 404, so crawlers lack a content-enumeration aid.",
            "suggested_action": "Publish sitemap.xml and reference it from robots.txt."
        })
    return recommendations


def compose_audit(site, include_proactive=True):
    """Compose findings, specialist statuses, and proactive recommendations."""
    domain, base_url = normalize_target(site)
    raw_findings = []
    specialists = {}
    specialist_recommendations = []
    all_observations = []
    all_coverage = {}
    all_limitations = []

    # --- Shared site inventory: one bounded acquisition pass. Specialists
    # operate on the SAME evidence snapshot (prevents inconsistent fetches,
    # avoids redundant crawling, keeps runtime inside the 5-minute budget).
    inventory, inv_stats = build_inventory(base_url)
    inventory_path = write_inventory_file(inventory) if inventory else None
    if inventory_path:
        all_coverage["site_inventory"] = inv_stats
        all_limitations.extend(inventory.get("limitations", []))
    elif inv_stats and not inv_stats.get("homepage_reachable", True):
        all_limitations.append("homepage unreachable: inventory could not be built")

    specialist_runs = [
        ("discoverability-audit", "Access, discovery & rendering risk", "discoverability_check.py"),
        ("entity-content-audit", "Entity identity & offer extractability", "entity_content_check.py"),
        ("fact-consistency-audit", "Fact ledger & cross-page consistency", "fact_consistency_check.py"),
        ("corroboration-authority-audit", "Declared-authority link verification", "corroboration_check.py"),
        ("engagement-context-audit", "Orientation & journey continuity", "engagement_check.py"),
    ]
    for skill_name, label, filename in specialist_runs:
        script = find_specialist_script(skill_name, filename)
        args = ["--site", base_url]
        if inventory_path:
            args += ["--inventory", inventory_path]
        status, findings, recs, error, observations, coverage, limitations = \
            run_specialist_tool(script, *args)
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

    all_recommendations = list(specialist_recommendations)
    if include_proactive:
        all_recommendations.extend(proactive_checks(domain, base_url))
    # Deduplicate by evidence prefix, highest severity first.
    # Fingerprint dedup: same logical check re-run across pages (or re-emitted
    # by two specialists) shares a normalized title; distinct checks keep
    # distinct titles. Far more robust than prefix-matching free-text evidence.
    def fingerprint(item):
        title = " ".join(str(item.get("title", "")).lower().split())
        return title

    final_findings = []
    seen = set()
    demoted = []  # findings failing the eligibility gate -> recommendations
    sorted_raw = sorted(raw_findings, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "medium"), 99))

    for item in sorted_raw:
        sev = str(item.get("severity", "medium")).lower()
        if sev not in SEVERITY_ORDER:
            sev = "medium"
        confidence = str(item.get("confidence", "medium")).lower()
        fp = fingerprint(item)
        if fp and fp in seen:
            continue
        if fp:
            seen.add(fp)
        evidence = str(item.get("evidence", "")).strip()
        # --- Eligibility gate: a defect finding must (a) cite concrete
        # evidence gathered during this run and (b) not be a high-severity
        # claim resting on low confidence. Failures become recommendations,
        # never silent drops.
        if len(evidence) < 10:
            demoted.append(dict(
                title=item.get("title", "Audit observation"),
                rationale=f"Specialist asserted '{item.get('title', '')}' without citing concrete evidence; "
                          "recorded as an improvement suggestion rather than a defect.",
                suggested_action=item.get("suggested_action", {}).get("summary", "Verify manually and add supporting evidence.")))
            continue
        if sev in ("critical", "high") and confidence == "low":
            demoted.append(dict(
                title=item.get("title", "Audit observation"),
                rationale=f"Potentially serious (originally '{sev}') but evidence confidence is low; "
                          "held as a suggestion pending stronger evidence rather than asserted as a defect.",
                suggested_action=item.get("suggested_action", {}).get("summary", "Verify manually.")))
            continue
        action = item.get("suggested_action", {})
        finding_entry = {
            "id": f"F-{len(final_findings) + 1:03d}",
            "title": item.get("title", "Audit Finding"),
            "severity": sev,
            "evidence": evidence,
            "suggested_action": {
                "summary": action.get("summary", "Review and resolve the identified defect."),
                "priority": action.get("priority", sev if sev != "info" else "low")
            }
        }
        # Preserve the rich evidence model when a specialist supplies it.
        for extra in ("category", "confidence", "root_cause", "impact", "verification", "scope"):
            if item.get(extra) is not None:
                finding_entry[extra] = item[extra]
        final_findings.append(finding_entry)

    all_recommendations.extend(demoted)

    summary_counts = {"total_findings": len(final_findings), "critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in final_findings:
        if f["severity"] in summary_counts:
            summary_counts[f["severity"]] += 1

    # --- Root-cause layer: cluster related findings under a shared cause so
    # the report recommends one prioritized action per cause, not N scattered
    # defects (operationalizes Round 2's root-cause requirement).
    root_causes = []
    rc_groups = {}
    for f in final_findings:
        rc = f.get("root_cause")
        if not rc:
            continue
        key = " ".join(str(rc).lower().split())[:120]
        g = rc_groups.setdefault(key, {"root_cause": str(f["root_cause"]), "finding_ids": [],
                                       "categories": set(), "severities": []})
        g["finding_ids"].append(f["id"])
        if f.get("category"):
            g["categories"].add(str(f["category"]))
        g["severities"].append(f["severity"])
    for g in rc_groups.values():
        worst = min(g["severities"], key=lambda s: SEVERITY_ORDER.get(s, 99))
        root_causes.append({
            "root_cause": g["root_cause"],
            "finding_ids": g["finding_ids"],
            "categories": sorted(g["categories"]),
            "max_severity": worst,
            "suggested_priority": worst if worst != "info" else "low",
        })
    root_causes.sort(key=lambda r: SEVERITY_ORDER.get(r["max_severity"], 99))

    # --- Diagnostic dimensions: internal diagnostic indices derived from
    # specialist status + finding mix. These are explicitly DIAGNOSTIC, not a
    # predictive "AI visibility score" (no single number predicts assistant
    # behavior; platforms measure visibility differently).
    diagnostic_dimensions = {}
    for name, skill, cats in (
        ("crawlability", "discoverability-audit", ("access", "rendering", "discovery")),
        ("entity_clarity", "entity-content-audit", ("entity-identity", "content-quality")),
        ("fact_integrity", "fact-consistency-audit", ("fact-consistency", "freshness")),
        ("citation_readiness", "corroboration-authority-audit", ("corroboration",)),
        ("context_continuity", "engagement-context-audit", ("orientation", "navigation")),
    ):
        if specialists.get(skill, {}).get("status") != "ok":
            continue
        hits = [f for f in final_findings if f.get("category") in cats]
        diagnostic_dimensions[name] = round(max(0.0, 100.0 - 10 * len(hits)), 1)

    report = {
        "site": domain,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary_counts,
        "specialists": specialists,
        "findings": final_findings,
    }
    if diagnostic_dimensions:
        report["diagnostic_dimensions"] = diagnostic_dimensions
        report["diagnostic_note"] = ("Diagnostic indices derived from this run's findings only. "
                                     "They are not a predictive ranking of AI-assistant visibility.")
    if root_causes:
        report["root_causes"] = root_causes
    if all_observations:
        report["observations"] = all_observations[:100]
    if all_coverage:
        report["coverage"] = all_coverage
    if all_limitations:
        report["limitations"] = all_limitations
    if all_recommendations:
        report["proactive_actions"] = all_recommendations
    return report


def validation_gate(report):
    """Run the bundled validator on the composed report before emitting.

    Returns True only if the report validates. On failure, diagnostics are
    written to stderr and the caller must NOT emit the report.
    """
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


def main():
    args = parse_args()
    report = compose_audit(args.site, include_proactive=args.include_proactive)

    if not validation_gate(report):
        sys.exit(1)

    output_json = json.dumps(report, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
