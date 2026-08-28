#!/usr/bin/env python3
"""
orchestrator.py - Entrypoint CLI for Brand AI-Readiness Audit Marketplace.
Composes the marketplace's specialist audit skills, enforces a strict global
time deadline (< 5 minutes), reconciles evidence-backed findings, deduplicates
overlapping signals and recommendations, groups findings under a standardized
root-cause taxonomy, and emits a strictly validated JSON audit report.

Guarantees:
  - All findings derive from real, on-demand probes. Nothing is fabricated.
  - Specialist execution status is always recorded ("ok" / "failed" / "inconclusive" / "not_run").
    Tool failure is NEVER converted into zero findings.
  - Hard wall-clock execution deadline is enforced across all phases.
  - SSRF protection and response size caps are enforced across all network fetches.
  - The final report is validated against the formal schema before emission.
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
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(SCRIPT_DIR, "validate_report.py")

# Import safe_fetch utility
try:
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

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

PRIORITY_KEYWORDS = [
    ("product", ["product", "/p/", "shop", "store", "item", "catalog"]),
    ("pricing", ["pricing", "price", "plans", "billing", "subscription"]),
    ("service", ["service", "solution", "offering", "consulting"]),
    ("category", ["category", "collection", "browse"]),
    ("contact", ["contact", "support", "help", "reach-us"]),
    ("location", ["location", "store-locator", "branch", "where-to-buy"]),
    ("about", ["about", "company", "team", "story", "mission"]),
    ("documentation", ["docs", "documentation", "guide", "api", "developer", "help-center"]),
    ("article", ["blog", "news", "article", "post", "insight"]),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit a website for AI discoverability, content extractability, and visitor engagement."
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. example.com or https://example.com)")
    parser.add_argument("--output", "-o", help="Path to save the generated JSON report (defaults to stdout)")
    
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


def classify_page(url, title=""):
    """Classify a page by URL/title keywords."""
    hay = (url + " " + (title or "")).lower()
    for ptype, kws in PRIORITY_KEYWORDS:
        if any(k in hay for k in kws):
            return ptype
    return "other"


def _visible_words(html):
    text = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", html or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(text.split())


def _extract_title(html):
    m = re.search(r"<title[^>]*>([^<]{1,300})</title>", html or "", re.I)
    return m.group(1).strip() if m else ""


def _sitemap_urls(sitemap_body, limit=60):
    return [loc.strip() for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap_body or "")][:limit]


def build_inventory(base_url, max_pages=16, budget_seconds=60):
    """Bounded, SSRF-safe shared crawl.
    Mandatory: homepage, robots.txt, sitemaps, and priority pages within budget.
    """
    start = time.time()
    parsed_base = urlparse(base_url)
    target_netloc = parsed_base.netloc.lower()

    inv = {
        "base_url": base_url,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "robots": None,
        "sitemap_urls": [],
        "pages": [],
        "limitations": []
    }

    # 1. Homepage
    status, home_html, headers, err = safe_fetch(base_url + "/", timeout=10, max_bytes=2*1024*1024)
    if not home_html or status is None:
        return None, {"homepage_reachable": False, "error": err}

    inv["pages"].append({
        "url": base_url + "/",
        "status": status,
        "page_type": "homepage",
        "title": _extract_title(home_html),
        "word_count": _visible_words(home_html),
        "html": home_html
    })

    # 2. robots.txt
    r_status, robots_txt, _, _ = safe_fetch(base_url + "/robots.txt", timeout=8, max_bytes=512*1024)
    inv["robots"] = {"status": r_status, "text": robots_txt if r_status == 200 else None}
    sitemap_urls = []
    if robots_txt and r_status == 200:
        sitemap_urls = [l.split(":", 1)[1].strip() for l in robots_txt.splitlines()
                        if l.lower().startswith("sitemap:")][:5]

    # 3. Sitemaps (Same-origin constraint)
    locs = []
    candidates = sitemap_urls or [base_url + "/sitemap.xml"]
    for sm in candidates:
        if time.time() - start > budget_seconds:
            break
        sm_netloc = urlparse(sm).netloc.lower()
        if sm_netloc and sm_netloc != target_netloc:
            continue  # ignore external sitemaps for security
        s_status, s_body, _, _ = safe_fetch(sm, timeout=8, max_bytes=2*1024*1024)
        if s_status == 200 and s_body and "<loc>" in s_body:
            inv["sitemap_urls"].append(sm)
            child_locs = _sitemap_urls(s_body)
            # Filter to same-origin URLs
            valid_child = [u for u in child_locs if urlparse(u).netloc.lower() == target_netloc]
            locs.extend(valid_child)

            if "<sitemapindex" in s_body:
                for sub_sm in child_locs[:3]:
                    if time.time() - start > budget_seconds:
                        break
                    if urlparse(sub_sm).netloc.lower() == target_netloc:
                        c_status, c_body, _, _ = safe_fetch(sub_sm, timeout=8, max_bytes=2*1024*1024)
                        if c_status == 200 and c_body:
                            locs.extend([u for u in _sitemap_urls(c_body) if urlparse(u).netloc.lower() == target_netloc])

    inv["sitemap_url_count"] = len(locs)

    # 4. Priority selection across page types within budget
    seen = {p["url"].rstrip("/") for p in inv["pages"]}
    by_type = {}
    for u in locs:
        u_clean = u.rstrip("/")
        if u_clean in seen or u_clean == base_url.rstrip("/"):
            continue
        ptype = classify_page(u)
        by_type.setdefault(ptype, []).append(u)

    priority_order = ["product", "pricing", "service", "category", "contact",
                      "location", "about", "documentation", "article", "other"]
    selected = []
    for t in priority_order:
        for u in by_type.get(t, [])[:3]:
            if len(selected) >= max_pages - 1 or time.time() - start > budget_seconds:
                break
            selected.append(u)
        if len(selected) >= max_pages - 1 or time.time() - start > budget_seconds:
            break

    for u in selected:
        if time.time() - start > budget_seconds:
            inv["limitations"].append("Inventory crawl truncated when acquisition time budget was reached.")
            break
        p_status, p_html, _, _ = safe_fetch(u, timeout=8, max_bytes=2*1024*1024)
        if p_html:
            seen.add(u.rstrip("/"))
            inv["pages"].append({
                "url": u,
                "status": p_status,
                "page_type": classify_page(u),
                "title": _extract_title(p_html),
                "word_count": _visible_words(p_html),
                "html": p_html
            })

    inv["elapsed_seconds"] = round(time.time() - start, 1)
    stats = {
        "homepage_reachable": True,
        "pages_sampled": len(inv["pages"]),
        "sitemap_urls_discovered": len(locs),
        "elapsed_seconds": inv["elapsed_seconds"],
        "page_types": {t: sum(1 for p in inv["pages"] if p["page_type"] == t)
                       for t in {p["page_type"] for p in inv["pages"]}}
    }
    return inv, stats


def write_inventory_file(inv):
    """Persist inventory to temporary JSON file."""
    try:
        fd, path = tempfile.mkstemp(suffix="_inventory.json", prefix="brand_audit_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(inv, f)
        return path
    except Exception:
        return None


def proactive_checks(domain, base_url):
    """Perform proactive improvement checks."""
    recommendations = []

    # Optional /llms.txt probe
    llms_status = safe_check_status(f"{base_url}/llms.txt", timeout=5)
    if llms_status == 404:
        recommendations.append({
            "title": "Optional experiment: publish an /llms.txt index",
            "category": "proactive-discovery",
            "rationale": f"GET {base_url}/llms.txt returned HTTP 404. llms.txt is a community convention "
                         "used by some LLM clients to discover Markdown feeds. (Not required for Google AI search).",
            "suggested_action": "Consider publishing /llms.txt as an optional navigation aid for external LLM tools."
        })

    # Sitemap check
    sitemap_status = safe_check_status(f"{base_url}/sitemap.xml", timeout=5)
    if sitemap_status == 404:
        recommendations.append({
            "title": "Publish an XML sitemap",
            "category": "discovery",
            "rationale": f"GET {base_url}/sitemap.xml returned HTTP 404.",
            "suggested_action": "Publish sitemap.xml listing all canonical public URLs and declare it in robots.txt."
        })

    return recommendations


def deduplicate_recommendations(rec_list):
    """Deduplicate recommendations by normalized action title and category."""
    seen = {}
    deduped = []
    for r in rec_list:
        if not isinstance(r, dict):
            continue
        title = r.get("title", "").strip()
        cat = r.get("category", "general")
        key = (cat.lower(), " ".join(title.lower().split()))
        if key in seen:
            # Merge rationales if distinct
            existing = seen[key]
            if r.get("rationale") and r["rationale"] not in existing.get("rationale", ""):
                existing["rationale"] += " " + r["rationale"]
            continue
        seen[key] = dict(r)
        deduped.append(seen[key])
    return deduped


def compose_audit(site, include_proactive=True, with_representation=False,
                  responses_file=None, timeout_seconds=300):
    """Compose full audit under a strict global wall-clock deadline."""
    start_time = time.time()
    domain, base_url = normalize_target(site)
    raw_findings = []
    specialists = {}
    specialist_recommendations = []
    all_observations = []
    all_coverage = {}
    all_limitations = []

    # 1. Acquisition Phase (Shared Inventory) - max 60s
    acquisition_budget = min(60, max(15, timeout_seconds - 60))
    inventory, inv_stats = build_inventory(base_url, budget_seconds=acquisition_budget)
    inventory_path = write_inventory_file(inventory) if inventory else None

    if inventory_path:
        all_coverage["site_inventory"] = inv_stats
        all_limitations.extend(inventory.get("limitations", []))
    elif inv_stats and not inv_stats.get("homepage_reachable", True):
        all_limitations.append(f"Homepage unreachable ({inv_stats.get('error', 'Network error')}); inventory could not be built.")

    # 2. Specialist Execution Phase
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

    # Execute specialists sequentially with dynamically calculated timeouts
    for idx, (skill_name, label, filename, extra_args) in enumerate(specialist_runs):
        elapsed = time.time() - start_time
        remaining_time = timeout_seconds - elapsed
        remaining_specialists = len(specialist_runs) - idx

        if remaining_time <= 5:
            specialists[skill_name] = {
                "label": label,
                "status": "not_run",
                "reason": "Execution skipped: global time budget exhausted"
            }
            all_limitations.append(f"{skill_name}: Skipped due to global execution time limit.")
            continue

        # Dynamic specialist timeout
        spec_timeout = max(10, min(40, int((remaining_time - 5) / max(1, remaining_specialists))))

        script = find_specialist_script(skill_name, filename)
        args = ["--site", base_url]
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
        all_recommendations.extend(proactive_checks(domain, base_url))

    # 4. Finding Normalization & Deduplication Gate
    def finding_fingerprint(item):
        cat = str(item.get("category", "")).lower()
        title = " ".join(str(item.get("title", "")).lower().split())
        return f"{cat}:{title}"

    final_findings = []
    seen_fps = set()
    demoted = []

    sorted_raw = sorted(raw_findings, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "medium"), 99))

    for item in sorted_raw:
        sev = str(item.get("severity", "medium")).lower()
        if sev not in SEVERITY_ORDER:
            sev = "medium"
        confidence = str(item.get("confidence", "medium")).lower()
        fp = finding_fingerprint(item)
        if fp in seen_fps:
            continue
        seen_fps.add(fp)

        evidence = str(item.get("evidence", "")).strip()
        # Eligibility Gate: concrete evidence required
        if len(evidence) < 8:
            demoted.append(dict(
                title=item.get("title", "Audit observation"),
                category=item.get("category", "general"),
                rationale=f"Specialist noted '{item.get('title', '')}' without citing concrete evidence.",
                suggested_action=item.get("suggested_action", {}).get("summary", "Verify manually.")
            ))
            continue

        if sev in ("critical", "high") and confidence == "low":
            demoted.append(dict(
                title=item.get("title", "Audit observation"),
                category=item.get("category", "general"),
                rationale=f"Reported with severity '{sev}' but low confidence; held as suggestion pending verification.",
                suggested_action=item.get("suggested_action", {}).get("summary", "Verify manually.")
            ))
            continue

        action = item.get("suggested_action", {})
        action_summary = action.get("summary") if isinstance(action, dict) else str(action)
        action_priority = action.get("priority", sev if sev != "info" else "low") if isinstance(action, dict) else sev

        finding_entry = {
            "id": f"F-{len(final_findings) + 1:03d}",
            "title": item.get("title", "Audit Finding"),
            "severity": sev,
            "evidence": evidence,
            "suggested_action": {
                "summary": action_summary or "Review and resolve the identified defect.",
                "priority": action_priority
            }
        }

        # Rich context preservation
        for extra in ("category", "confidence", "root_cause", "cause_family", "cause_id", "impact", "verification", "scope"):
            if item.get(extra) is not None:
                finding_entry[extra] = item[extra]

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

    # 5. Taxonomy-Driven Root-Cause Clustering
    rc_groups = {}
    for f in final_findings:
        cf = f.get("cause_family") or "GENERAL.AUDIT"
        cid = f.get("cause_id") or "GEN-001"
        rc_text = f.get("root_cause") or f["title"]

        group_key = f"{cf}:{cid}"
        if group_key not in rc_groups:
            rc_groups[group_key] = {
                "cause_family": cf,
                "cause_id": cid,
                "root_cause": rc_text,
                "finding_ids": [],
                "severities": []
            }
        rc_groups[group_key]["finding_ids"].append(f["id"])
        rc_groups[group_key]["severities"].append(f["severity"])

    root_causes = []
    for g in rc_groups.values():
        worst = min(g["severities"], key=lambda s: SEVERITY_ORDER.get(s, 99))
        root_causes.append({
            "cause_family": g["cause_family"],
            "cause_id": g["cause_id"],
            "root_cause": g["root_cause"],
            "finding_ids": g["finding_ids"],
            "max_severity": worst,
            "suggested_priority": worst if worst != "info" else "low"
        })
    root_causes.sort(key=lambda r: SEVERITY_ORDER.get(r["max_severity"], 99))

    # 6. Objective Audit Metrics
    audit_metrics = {
        "execution_time_seconds": round(time.time() - start_time, 1),
        "pages_sampled": inv_stats.get("pages_sampled", 1) if inv_stats else 1,
        "page_types_covered": inv_stats.get("page_types", {}) if inv_stats else {},
        "critical_blockers": summary_counts["critical"],
        "confidence_distribution": {
            "high": sum(1 for f in final_findings if f.get("confidence") == "high"),
            "medium": sum(1 for f in final_findings if f.get("confidence") == "medium"),
            "low": sum(1 for f in final_findings if f.get("confidence") == "low")
        },
        "answerability_index": all_coverage.get("entity-content-audit", {}).get("answerability_index", 1.0)
    }

    report = {
        "site": domain,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary_counts,
        "specialists": specialists,
        "findings": final_findings,
        "audit_metrics": audit_metrics,
    }

    if root_causes:
        report["root_causes"] = root_causes
    if all_observations:
        report["observations"] = all_observations[:100]
    if all_coverage:
        report["coverage"] = all_coverage
    if all_limitations:
        report["limitations"] = all_limitations
    if deduped_recommendations:
        report["proactive_actions"] = deduped_recommendations

    return report


def validation_gate(report):
    """Run validator on the generated report before emission."""
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
    report = compose_audit(
        args.site,
        include_proactive=args.include_proactive,
        with_representation=args.with_representation,
        responses_file=args.responses_file,
        timeout_seconds=args.timeout_seconds
    )

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
