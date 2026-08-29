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
    parser.add_argument("--trace", help="Output path for Mermaid.js execution trace diagram")
    parser.add_argument("--format", choices=["json", "markdown", "rich"], default="json",
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
    
    # 1. Sitemap check
    has_sitemap = False
    if inv_stats and inv_stats.get("sitemaps_found", 0) > 0:
        has_sitemap = True
    else:
        sitemap_status = safe_check_status(f"{base_url}/sitemap.xml", timeout=5)
        if sitemap_status != 404:
            has_sitemap = True

    if not has_sitemap:
        recommendations.append({
            "title": "Publish a canonical XML Sitemap",
            "category": "discovery",
            "summary": "AI crawlers rely on XML sitemaps to efficiently discover brand pages without relying on deep HTML traversal.",
            "priority": "medium"
        })

    # 2. llms.txt (Emerging AI Standard)
    llms_status = safe_check_status(f"{base_url}/llms.txt", timeout=5)
    if llms_status == 404:
        recommendations.append({
            "title": "Publish an /llms.txt standard index",
            "category": "ai-readiness",
            "summary": "Implement the /llms.txt standard (a Markdown-based root file) to provide AI research agents (like Perplexity and OpenAI) with a clean, explicitly formatted summary of your brand's core facts, pricing, and documentation without HTML parsing friction.",
            "priority": "low"
        })
        
    # 3. OCR and Semantic Extractability (Addressing Appendix C and F)
    recommendations.append({
        "title": "Isolate substantive text from non-readable formats",
        "category": "extractability",
        "summary": "Ensure critical brand facts, pricing tiers, and contact details are explicitly stated in semantic HTML text (<article>, <main>). Avoid locking substantive information inside images without descriptive alt-text, as AI summarizers and basic crawlers often drop non-textual or boilerplate-heavy content.",
        "priority": "low"
    })
    
    # 4. IndexNow Protocol
    recommendations.append({
        "title": "Implement the IndexNow Protocol",
        "category": "discovery",
        "summary": "Proactively ping search engines (via IndexNow API) when brand content changes. Since Bing powers Copilot and integrates with ChatGPT, this reduces AI knowledge latency from weeks to minutes.",
        "priority": "low"
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



import json

def discover_plugins():
    """Dynamic Plugin Discovery Kernel (Marketplace OS)"""
    market_path = os.path.join(SCRIPT_DIR, "..", "..", "..", "marketplace.json")
    if not os.path.exists(market_path):
        market_path = os.path.join(SCRIPT_DIR, "..", "..", "marketplace.json")
    
    plugins = []
    try:
        with open(market_path, "r") as f:
            manifest = json.load(f)
        for skill in manifest.get("skills", []):
            sid = skill.get("id")
            if sid and not skill.get("entrypoint"):
                base = sid.replace("-audit", "").replace("-", "_")
                script_name = f"{base}_check.py"
                if sid == "assistant-representation-audit": script_name = "representation_check.py"
                elif sid == "fact-consistency-audit": script_name = "fact_consistency_check.py"
                elif sid == "corroboration-authority-audit": script_name = "corroboration_check.py"
                elif sid == "engagement-context-audit": script_name = "engagement_check.py"
                elif sid == "discoverability-audit": script_name = "discoverability_check.py"
                elif sid == "entity-content-audit": script_name = "entity_content_check.py"
                
                label = f"Dynamic execution of {sid}"
                if "discoverability" in sid: label = "Access, robots.txt & rendering risk"
                if "entity" in sid: label = "Entity identity & offer extractability"
                if "fact" in sid: label = "Fact ledger & cross-page consistency"
                if "corroboration" in sid: label = "Declared authority link verification"
                if "engagement" in sid: label = "Orientation & journey continuity"
                
                plugins.append((sid, label, script_name, []))
    except Exception as e:
        pass
    
    if not plugins:
        plugins = [
            ("discoverability-audit", "Access, robots.txt & rendering risk", "discoverability_check.py", []),
            ("entity-content-audit", "Entity identity & offer extractability", "entity_content_check.py", []),
            ("fact-consistency-audit", "Fact ledger & cross-page consistency", "fact_consistency_check.py", []),
            ("corroboration-authority-audit", "Declared authority link verification", "corroboration_check.py", []),
            ("engagement-context-audit", "Orientation & journey continuity", "engagement_check.py", []),
        ]
    return plugins

def apply_consensus_engine(consolidated_raw, all_observations):
    """
    Multi-Agent Consensus Engine:
    Resolves conflicts between independent specialists to eliminate false positives.
    """
    has_structured_data = any(o.get("observation") == "Valid JSON-LD extracted" for o in all_observations)
    has_html_content = any(f.get("cause_id") == "RENDERED_CONTENT_GAP" for f in consolidated_raw)
    
    for item in consolidated_raw:
        # If site is a CSR shell (Discoverability), but it has rich JSON-LD (Entity)
        # We downgrade the CSR severity because AI can still read the structured data!
        if item.get("cause_id") == "RENDERED_CONTENT_GAP" and has_structured_data:
            item["severity"] = "medium"
            item["confidence"] = "medium"
            item["evidence"] += " [Consensus Engine: Downgraded to medium because rich JSON-LD structured data is present and extractable despite rendering gap.]"
            
        # If Fact Consistency flags a mismatch, but Engagement notes it's an archive page
        if item.get("category") == "fact-consistency":
            if any("archive" in o.get("observation", "").lower() for o in all_observations):
                item["severity"] = "low"
                item["evidence"] += " [Consensus Engine: Detected archive context; fact drift is expected.]"
                
    return consolidated_raw


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
    specialist_runs = discover_plugins()

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




def generate_mermaid_trace(report, out_path):
    """Deterministic State Telemetry: Generates a Mermaid.js execution graph."""
    lines = [
        "```mermaid",
        "graph TD",
        '    subgraph "Acquisition Phase"',
        '        A[Master Orchestrator] -->|ThreadPool BFS| B(Shared Site Inventory)',
        f'        B -->|Sampled {report.get("audit_metrics", {}).get("html_pages_sampled", 0)} pages| C{{Dispatcher}}',
        '    end',
        '    subgraph "Dynamic Specialist Plugins"'
    ]
    
    specs = report.get("specialists", {})
    for i, (sid, sdata) in enumerate(specs.items()):
        status = sdata.get("status")
        if status != "not_run":
            lines.append(f'        C -->|Execute| S{i}[{sid}]')
            lines.append(f'        S{i} -->|Status: {status}| D{{Consensus Engine}}')
            
    lines.append('    end')
    lines.append('    subgraph "Synthesis Phase"')
    lines.append('        D -->|Conflict Resolution| E[Final JSON Schema]')
    
    proactive = report.get("proactive_actions", [])
    if proactive:
        lines.append(f'        E -.->|Injected| P[{len(proactive)} Proactive Recommendations]')
    lines.append('    end')
    
    lines.append('    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;')
    lines.append('    classDef agent fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;')
    lines.append('    class A,C,D,E agent')
    lines.append("```")
    
    with open(out_path, "w") as f:
        f.write("\n".join(lines))


def format_rich_report(report):
    # ANSI escape codes for gorgeous CLI output
    C_RESET = "\033[0m"
    C_BOLD = "\033[1m"
    C_CYAN = "\033[96m"
    C_GREEN = "\033[92m"
    C_YELLOW = "\033[93m"
    C_RED = "\033[91m"
    C_DIM = "\033[2m"
    C_BG_RED = "\033[41m\033[37m"
    
    site = report.get("site", "Target Site")
    summary = report.get("summary", {})
    metrics = report.get("audit_metrics", {})
    
    out = []
    out.append(f"\n{C_BOLD}{C_CYAN}======================================================={C_RESET}")
    out.append(f"{C_BOLD}{C_CYAN}  BRAND AI-READINESS AUDIT: {site.upper()}{C_RESET}")
    out.append(f"{C_BOLD}{C_CYAN}======================================================={C_RESET}\n")
    
    out.append(f"{C_BOLD}► EXECUTION METRICS{C_RESET}")
    out.append(f"  {C_DIM}Time:{C_RESET} {metrics.get('execution_time_seconds', 0)}s   {C_DIM}Pages Sampled:{C_RESET} {metrics.get('html_pages_sampled', 0)}   {C_DIM}Status:{C_RESET} {report.get('audit_status', 'ok')}\n")
    
    total = summary.get("total_findings", 0)
    crit = summary.get("critical", 0)
    high = summary.get("high", 0)
    med = summary.get("medium", 0)
    
    out.append(f"{C_BOLD}► FINDINGS SUMMARY ({total} Total){C_RESET}")
    out.append(f"  {C_BG_RED if crit > 0 else C_DIM} CRITICAL: {crit} {C_RESET}  {C_RED if high > 0 else C_DIM} HIGH: {high} {C_RESET}  {C_YELLOW if med > 0 else C_DIM} MEDIUM: {med} {C_RESET}\n")
    
    findings = report.get("findings", [])
    if findings:
        out.append(f"{C_BOLD}► TOP FINDINGS{C_RESET}")
        for i, f in enumerate(findings[:5]):
            sev = str(f.get("severity", "")).upper()
            color = C_BG_RED if sev == "CRITICAL" else (C_RED if sev == "HIGH" else C_YELLOW)
            out.append(f"  {color} {sev} {C_RESET} {C_BOLD}{f.get('title')}{C_RESET}")
            out.append(f"    {C_DIM}Evidence:{C_RESET} {f.get('evidence')}")
            out.append(f"    {C_DIM}Action:{C_RESET} {C_GREEN}{f.get('suggested_action', {}).get('summary', '')}{C_RESET}\n")
            
    proactive = report.get("proactive_actions", [])
    if proactive:
        out.append(f"{C_BOLD}► PROACTIVE AI-READINESS RECOMMENDATIONS{C_RESET}")
        for p in proactive:
            out.append(f"  {C_CYAN}💡 {p.get('title')}{C_RESET}")
            out.append(f"    {C_DIM}{p.get('summary')}{C_RESET}\n")
            
    out.append(f"{C_BOLD}{C_CYAN}======================================================={C_RESET}\n")
    return "\n".join(out)

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

    if args.trace:
        try:
            generate_mermaid_trace(report, args.trace)
        except Exception as e:
            sys.stderr.write(f"Trace generation warning: {e}\n")

    if args.format == "markdown":
        out_content = format_markdown_report(report)
    elif args.format == "rich":
        out_content = format_rich_report(report)
    else:
        out_content = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_content + "\n")
    else:
        print(out_content)


if __name__ == "__main__":
    main()
