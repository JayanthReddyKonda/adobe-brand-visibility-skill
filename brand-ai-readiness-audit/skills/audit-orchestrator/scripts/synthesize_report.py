#!/usr/bin/env python3
"""
synthesize_report.py - Master synthesis engine for Brand AI-Readiness Audit Marketplace.
Takes collected specialist outputs, deduplicates overlapping signals, clusters findings
under the unified causal failure taxonomy, compiles objective coverage metrics, and
emits a strictly validated JSON report conforming to the Adobe Round 3 schema.
"""

import sys
import os
import re
import json
import time
import argparse
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(SCRIPT_DIR, "validate_report.py")

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def parse_args():
    parser = argparse.ArgumentParser(description="Synthesize specialist outputs into final audit report.")
    parser.add_argument("--site", required=True, help="Target website domain or URL")
    parser.add_argument("--inventory", help="Path to site inventory JSON")
    parser.add_argument("--discoverability", help="Path to discoverability-audit result JSON")
    parser.add_argument("--entity", help="Path to entity-content-audit result JSON")
    parser.add_argument("--fact", help="Path to fact-consistency-audit result JSON")
    parser.add_argument("--corroboration", help="Path to corroboration-authority-audit result JSON")
    parser.add_argument("--engagement", help="Path to engagement-context-audit result JSON")
    parser.add_argument("--representation", help="Path to assistant-representation-audit result JSON")
    parser.add_argument("--output", "-o", help="Path to save output JSON")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    parser.add_argument("--db", help="Path to SQLite database to record audit history (optional)")
    return parser.parse_args()



def load_json_file(path):
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


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


def synthesize(site_input, inv=None, d_res=None, e_res=None, f_res=None, c_res=None, eng_res=None, rep_res=None, start_time=None):
    domain = site_input.strip().split("://")[-1].split("/")[0]
    raw_findings = []
    specialists = {}
    all_recommendations = []
    all_observations = []
    all_coverage = {}
    all_limitations = []

    # Map specialists
    specs = [
        ("discoverability-audit", "Access, robots.txt & rendering risk", d_res),
        ("entity-content-audit", "Entity identity & offer extractability", e_res),
        ("fact-consistency-audit", "Fact ledger & cross-page consistency", f_res),
        ("corroboration-authority-audit", "Declared authority link verification", c_res),
        ("engagement-context-audit", "Orientation & journey continuity", eng_res),
    ]

    for name, label, res in specs:
        if res is None:
            specialists[name] = {"label": label, "status": "not_run", "reason": "No specialist output provided"}
            continue
        st = str(res.get("status", "ok")).lower()
        specialists[name] = {"label": label, "status": st}
        if res.get("error"):
            specialists[name]["error"] = res["error"]
        if res.get("coverage"):
            all_coverage[name] = res["coverage"]
        all_limitations.extend(f"{name}: {l}" for l in res.get("limitations", []))
        for obs in res.get("observations", []):
            if isinstance(obs, dict) and obs.get("observation"):
                all_observations.append(obs)
        raw_findings.extend(res.get("findings", []))
        all_recommendations.extend(res.get("recommendations", []))

    if rep_res is not None:
        st = str(rep_res.get("status", "ok")).lower()
        specialists["assistant-representation-audit"] = {"label": "Observed assistant representation cross-check", "status": st}
        if rep_res.get("error"):
            specialists["assistant-representation-audit"]["error"] = rep_res["error"]
        if rep_res.get("coverage"):
            all_coverage["assistant-representation-audit"] = rep_res["coverage"]
        all_limitations.extend(f"assistant-representation-audit: {l}" for l in rep_res.get("limitations", []))
        raw_findings.extend(rep_res.get("findings", []))
        all_recommendations.extend(rep_res.get("recommendations", []))
    else:
        specialists["assistant-representation-audit"] = {
            "label": "Observed assistant representation cross-check",
            "status": "not_run",
            "reason": "Optional representation layer disabled (run with --with-representation to enable)"
        }

    # Extract inventory stats
    if inv is not None:
        html_pages = [p for p in inv.get("pages", []) if p.get("resource_type") == "html" or p.get("page_type")]
        all_coverage["site_inventory"] = {
            "html_pages_sampled": len(html_pages),
            "sitemaps_processed": inv.get("infrastructure", {}).get("sitemaps_processed", 0),
            "urls_discovered": inv.get("infrastructure", {}).get("urls_extracted", 0),
            "page_types": {t: sum(1 for p in html_pages if p.get("page_type") == t)
                           for t in {p.get("page_type") for p in html_pages if p.get("page_type")}}
        }
        all_limitations.extend(inv.get("limitations", []))

    # Multi-Locale Finding Consolidation & Deduplication Gate
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

    return report



def main():
    start = time.time()
    args = parse_args()
    inv = load_json_file(args.inventory)
    d_res = load_json_file(args.discoverability)
    e_res = load_json_file(args.entity)
    f_res = load_json_file(args.fact)
    c_res = load_json_file(args.corroboration)
    eng_res = load_json_file(args.engagement)
    rep_res = load_json_file(args.representation)

    report = synthesize(args.site, inv=inv, d_res=d_res, e_res=e_res, f_res=f_res, c_res=c_res, eng_res=eng_res, rep_res=rep_res, start_time=start)


    # Validate against schema
    try:
        proc = subprocess.run(
            [sys.executable, VALIDATOR, "-", "--quiet"],
            input=json.dumps(report), capture_output=True, text=True, timeout=30
        )
        if proc.returncode != 0:
            sys.stderr.write("Validation failed:\n" + (proc.stderr or "invalid schema") + "\n")
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Validator error: {e}\n")
        sys.exit(1)

    # Save to SQLite if requested
    if args.db:
        try:
            from audit_db import save_audit_report
            save_audit_report(report, db_path=args.db)
        except Exception as e:
            sys.stderr.write(f"SQLite save warning: {e}\n")

    out_json = json.dumps(report, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json + "\n")
    else:
        print(out_json)


if __name__ == "__main__":
    main()


