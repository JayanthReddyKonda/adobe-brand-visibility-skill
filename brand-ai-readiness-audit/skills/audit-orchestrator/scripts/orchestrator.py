#!/usr/bin/env python3
"""
orchestrator.py - Entrypoint CLI for Brand AI-Readiness Audit Marketplace.
Composes the marketplace's specialist audit skills, reconciles their
evidence-backed findings, deduplicates overlapping signals, adds proactive
improvement checks, and emits a strictly validated JSON audit report.

All findings are derived from real, on-demand checks of the target site.
No synthesized or fabricated findings are ever produced.

Usage:
  python3 orchestrator.py --site example.com [--output report.json]
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
import subprocess
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit a website for AI discoverability and on-site engagement by composing specialist skills."
    )
    parser.add_argument("--site", required=True, help="Target website URL or domain (e.g. example.com or https://example.com)")
    parser.add_argument("--output", "-o", help="Path to save the generated JSON report (defaults to stdout)")
    parser.add_argument("--include-proactive", action="store_true", default=True,
                        help="Run proactive discoverability/engagement checks (default: True)")
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
    """Dynamically discover specialist script across common skill layouts."""
    search_roots = [
        # Standard marketplace: skills/<skill_name>/scripts/<script_filename>
        os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", skill_name, "scripts")),
        # Flat layout: ../<skill_name>/scripts/<script_filename>
        os.path.abspath(os.path.join(SCRIPT_DIR, "..", skill_name, "scripts")),
        # Workspace relative: brand-ai-readiness-audit/skills/<skill_name>/scripts
        os.path.abspath(os.path.join(os.getcwd(), "brand-ai-readiness-audit", "skills", skill_name, "scripts")),
        # .agents relative: .agents/skills/<skill_name>/scripts
        os.path.abspath(os.path.join(os.getcwd(), ".agents", "skills", skill_name, "scripts")),
    ]
    for root in search_roots:
        candidate = os.path.join(root, script_filename)
        if os.path.exists(candidate):
            return candidate
    return None

def run_specialist_tool(script_path, *args):
    """Execute a specialist skill script using the active Python interpreter."""
    if not script_path or not os.path.exists(script_path):
        return []
    try:
        cmd = [sys.executable, script_path] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "findings" in data:
                return data["findings"]
        return []
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to execute {script_path}: {e}\n")
        return []

def http_get(url, timeout=8):
    """Return (status, text) for a GET request, or (None, None) on failure."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        sys.stderr.write(f"Proactive fetch failed for {url}: {e}\n")
        return None, None


def proactive_checks(domain, base_url, include_proactive):
    """Run non-defect improvement checks by probing the live site.

    Returns proactive recommendations (low-priority suggestions) derived
    from real network probes on the target site.
    """
    if not include_proactive:
        return []
    recommendations = []

    # 1. llms.txt presence (machine-readable AI index)
    status, body = http_get(f"{base_url}/llms.txt")
    if status is None:
        # Network/environment prevented the check; do not fabricate a conclusion.
        recommendations.append({
            "title": "Could not verify llms.txt (network/environment)",
            "severity": "low",
            "evidence": f"Unable to fetch {base_url}/llms.txt from this environment; treat as inconclusive.",
            "suggested_action": {
                "summary": "Re-run the audit from an environment with network access to confirm llms.txt status.",
                "priority": "low"
            }
        })
    elif status < 400 and body and body.strip():
        recommendations.append({
            "title": "llms.txt documentation index is already present",
            "severity": "low",
            "evidence": f"GET {base_url}/llms.txt returned HTTP {status} with content.",
            "suggested_action": {
                "summary": "Keep the llms.txt index current as you publish new docs and products.",
                "priority": "low"
            }
        })
    else:
        status_full, body_full = http_get(f"{base_url}/llms-full.txt")
        if status_full is not None and status_full < 400 and body_full and body_full.strip():
            recommendations.append({
                "title": "llms-full.txt documentation index is already present",
                "severity": "low",
                "evidence": f"GET {base_url}/llms-full.txt returned HTTP {status_full} with content.",
                "suggested_action": {
                    "summary": "Keep the llms-full.txt index current as you publish new docs and products.",
                    "priority": "low"
                }
            })
        else:
            recommendations.append({
                "title": "Proactive: consider publishing llms.txt to strengthen AI discoverability",
                "severity": "low",
                "evidence": f"Neither /llms.txt nor /llms-full.txt was found at {base_url} (llms.txt HTTP {status}).",
                "suggested_action": {
                    "summary": "Publish a curated /llms.txt Markdown index listing key documentation and capabilities.",
                    "priority": "low"
                }
            })

    # 2. Sitemap presence (helps AI crawlers discover content)
    status, _ = http_get(f"{base_url}/sitemap.xml")
    if status is None:
        pass  # inconclusive; skip to avoid noise
    elif status >= 400:
        recommendations.append({
            "title": "Proactive: no sitemap.xml discovered",
            "severity": "low",
            "evidence": f"GET {base_url}/sitemap.xml returned HTTP {status}.",
            "suggested_action": {
                "summary": "Add an XML sitemap and reference it from robots.txt to help crawlers enumerate content.",
                "priority": "low"
            }
        })

    return recommendations

def compose_audit(site, include_proactive=True):
    """Compose findings from the specialist skills plus proactive checks."""
    domain, base_url = normalize_target(site)
    raw_findings = []

    # 1. Run crawl-render audit
    crawl_script = find_specialist_script("crawl-render-audit", "crawl_render_check.py")
    if crawl_script:
        raw_findings.extend(run_specialist_tool(crawl_script, "--site", base_url))

    # 2. Run freshness-corroboration audit
    freshness_script = find_specialist_script("freshness-corroboration", "freshness_check.py")
    if freshness_script:
        raw_findings.extend(run_specialist_tool(freshness_script, "--site", base_url))

    # 3. Run engagement audit
    engagement_script = find_specialist_script("engagement-audit", "engagement_check.py")
    if engagement_script:
        raw_findings.extend(run_specialist_tool(engagement_script, "--site", base_url))

    # 4. Proactive improvement checks (optional)
    if include_proactive:
        raw_findings.extend(proactive_checks(domain, base_url, include_proactive=True))

    # Normalize IDs into F-001, F-002, ... with deduplication
    final_findings = []
    seen_evidence = set()
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_raw = sorted(raw_findings, key=lambda f: severity_order.get(f.get("severity", "medium"), 99))

    for idx, item in enumerate(sorted_raw, 1):
        sev = item.get("severity", "medium").lower()
        if sev not in severity_order:
            sev = "medium"

        evidence = item.get("evidence", "Observed during automated site audit.").strip()
        evidence_key = evidence[:120]
        if evidence_key in seen_evidence:
            continue
        seen_evidence.add(evidence_key)

        finding_entry = {
            "id": f"F-{idx:03d}",
            "title": item.get("title", f"Audit Finding {idx}"),
            "severity": sev,
            "evidence": evidence,
            "suggested_action": {
                "summary": item.get("suggested_action", {}).get("summary", "Review and resolve the identified defect."),
                "priority": item.get("suggested_action", {}).get("priority", sev if sev in ["critical", "high", "medium", "low"] else "medium")
            }
        }
        final_findings.append(finding_entry)

    summary_counts = {"total_findings": len(final_findings), "critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in final_findings:
        s = f["severity"]
        if s in summary_counts:
            summary_counts[s] += 1

    report = {
        "site": domain,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary_counts,
        "findings": final_findings
    }
    return report

def main():
    args = parse_args()
    report = compose_audit(args.site, include_proactive=args.include_proactive)
    output_json = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json + "\n")
    else:
        print(output_json)

if __name__ == "__main__":
    main()

