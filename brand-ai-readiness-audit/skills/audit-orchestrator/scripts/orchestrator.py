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
from acquire_inventory import build_inventory, classify_page, normalize_target, is_html_response

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


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
    start_mono = time.monotonic()
    monotonic_deadline = start_mono + timeout_seconds
    domain, base_url = normalize_target(site)
    raw_findings = []
    specialists = {}
    specialist_recommendations = []
    all_observations = []
    all_coverage = {}
    all_limitations = []

    # 1. Acquisition Phase (Type-Safe Shared Inventory) - max 60s
    acquisition_deadline = min(monotonic_deadline, start_mono + 60)
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
        now = time.monotonic()
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

    # Determine audit_status
    active_statuses = [info.get("status") for k, info in specialists.items() if info.get("status") != "not_run"]
    if not inv_stats or not inv_stats.get("homepage_reachable", True):
        audit_status = "inconclusive"
    elif all(st == "inconclusive" for st in active_statuses):
        audit_status = "inconclusive"
    elif any(st in ("failed", "inconclusive") for st in active_statuses):
        audit_status = "partial"
    else:
        audit_status = "ok"

    audit_metrics = {
        "execution_time_seconds": round(time.monotonic() - start_mono, 1),
        "html_pages_sampled": inv_stats.get("html_pages_sampled", 0) if inv_stats else 0,
        "sitemaps_processed": inv_stats.get("sitemaps_processed", 0) if inv_stats else 0,
        "urls_discovered": inv_stats.get("urls_discovered", 0) if inv_stats else 0,
        "page_types_covered": inv_stats.get("page_types", {}) if inv_stats else {},
        "critical_blockers": summary_counts["critical"]
    }

    report = {
        "site": domain,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audit_status": audit_status,
        "summary": summary_counts,
        "specialists": specialists,
        "audit_metrics": audit_metrics,
        "coverage": all_coverage,
        "findings": final_findings,
        "proactive_actions": deduped_recommendations,
        "observations": all_observations[:100],
        "limitations": all_limitations
    }

    internal_telemetry = {
        "specialists": specialists,
        "audit_metrics": audit_metrics,
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
