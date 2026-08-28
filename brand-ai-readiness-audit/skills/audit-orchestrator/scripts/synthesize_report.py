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
        cat = r.get("category", "general")
        key = (cat.lower(), " ".join(title.lower().split()))
        if key in seen:
            existing = seen[key]
            if r.get("rationale") and r["rationale"] not in existing.get("rationale", ""):
                existing["rationale"] += " " + r["rationale"]
            continue
        seen[key] = dict(r)
        deduped.append(seen[key])
    return deduped


def synthesize(site_input, inv=None, d_res=None, e_res=None, f_res=None, c_res=None, eng_res=None, rep_res=None):
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
        raw_findings.extend(rep_res.get("findings", []))
        all_recommendations.extend(rep_res.get("recommendations", []))
    else:
        specialists["assistant-representation-audit"] = {
            "label": "Observed assistant representation cross-check",
            "status": "not_run",
            "reason": "Optional representation layer disabled"
        }

    # Inventory coverage
    if inv:
        pages = inv.get("pages", [])
        html_pages = [p for p in pages if p.get("resource_type") == "html" or p.get("page_type") == "homepage"]
        all_coverage["site_inventory"] = {
            "homepage_reachable": True,
            "html_pages_sampled": len(html_pages),
            "sitemaps_found": len((inv.get("infrastructure") or {}).get("sitemaps_discovered", [])),
            "sitemaps_processed": (inv.get("infrastructure") or {}).get("sitemaps_processed", 0),
            "urls_discovered": (inv.get("infrastructure") or {}).get("urls_extracted", 0),
            "page_types": {t: sum(1 for p in html_pages if p.get("page_type") == t)
                           for t in {p.get("page_type") for p in html_pages if p.get("page_type")}}
        }
        all_limitations.extend(inv.get("limitations", []))

    # Finding Normalization & Deduplication Gate
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

    # Taxonomy-Driven Root-Cause Clustering
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

    # Objective Audit Metrics
    audit_metrics = {
        "execution_time_seconds": round(time.time() - start_time, 1) if start_time else 0.5,
        "html_pages_sampled": all_coverage.get("site_inventory", {}).get("html_pages_sampled", 1),
        "sitemaps_processed": all_coverage.get("site_inventory", {}).get("sitemaps_processed", 0),
        "urls_discovered": all_coverage.get("site_inventory", {}).get("urls_discovered", 0),
        "page_types_covered": all_coverage.get("site_inventory", {}).get("page_types", {}),
        "critical_blockers": summary_counts["critical"],
        "confidence_distribution": {
            "high": sum(1 for f in final_findings if f.get("confidence") == "high"),
            "medium": sum(1 for f in final_findings if f.get("confidence") == "medium"),
            "low": sum(1 for f in final_findings if f.get("confidence") == "low")
        }
    }


    ans_index = all_coverage.get("entity-content-audit", {}).get("answerability_index")
    if ans_index is not None:
        audit_metrics["answerability_index"] = ans_index

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


