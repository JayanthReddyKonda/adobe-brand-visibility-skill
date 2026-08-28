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
import json
import argparse
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
        return "not_run", [], [], "specialist script not found"
    try:
        cmd = [sys.executable, script_path] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            err = (proc.stderr or "non-zero exit").strip().splitlines()
            return "failed", [], [], err[-1] if err else "non-zero exit"
        if not proc.stdout.strip():
            return "failed", [], [], "no output produced"
        data = json.loads(proc.stdout)
        if isinstance(data, list):
            return "ok", data, [], None
        if isinstance(data, dict):
            findings = data.get("findings", [])
            recs = data.get("recommendations", [])
            if not isinstance(findings, list) or not isinstance(recs, list):
                return "failed", [], [], "unrecognized output format"
            # Honor the specialist's own self-reported status: an
            # "inconclusive"/"failed" specialist must never be recorded as
            # "ok" with zero findings (that would masquerade as a clean site).
            sp_status = str(data.get("status", "ok")).lower()
            if sp_status in ("ok", "success"):
                return "ok", findings, recs, None
            if sp_status == "inconclusive":
                return "inconclusive", [], [], data.get("error", "specialist could not gather evidence")
            return "failed", [], [], data.get("error", f"specialist reported status '{sp_status}'")
    except subprocess.TimeoutExpired:
        return "failed", [], [], "timed out after 60s"
    except Exception as e:
        return "failed", [], [], str(e)

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

    specialist_runs = [
        ("discoverability-audit", "Access, discovery & rendering risk", "discoverability_check.py"),
        ("entity-content-audit", "Entity identity & offer extractability", "entity_content_check.py"),
        ("fact-consistency-audit", "Fact ledger & cross-page consistency", "fact_consistency_check.py"),
        ("corroboration-authority-audit", "Declared-authority link verification", "corroboration_check.py"),
        ("engagement-context-audit", "Orientation & journey continuity", "engagement_check.py"),
    ]
    for skill_name, label, filename in specialist_runs:
        script = find_specialist_script(skill_name, filename)
        status, findings, recs, error = run_specialist_tool(script, "--site", base_url)
        specialists[skill_name] = {"label": label, "status": status}
        if error:
            specialists[skill_name]["error"] = error
        raw_findings.extend(findings)
        specialist_recommendations.extend(recs)

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
    sorted_raw = sorted(raw_findings, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "medium"), 99))

    for item in sorted_raw:
        sev = str(item.get("severity", "medium")).lower()
        if sev not in SEVERITY_ORDER:
            sev = "medium"
        fp = fingerprint(item)
        if fp and fp in seen:
            continue
        if fp:
            seen.add(fp)
        evidence = str(item.get("evidence", "")).strip() or "Observed during automated site audit."
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

    summary_counts = {"total_findings": len(final_findings), "critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in final_findings:
        if f["severity"] in summary_counts:
            summary_counts[f["severity"]] += 1

    report = {
        "site": domain,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary_counts,
        "specialists": specialists,
        "findings": final_findings,
    }
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
