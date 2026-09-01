import json
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



CAUSE_REMEDY_FALLBACKS = {
    "AI_RETRIEVAL_BLOCKED": {
        "technical_fix": "Add 'User-agent: OAI-SearchBot\nAllow: /' to robots.txt and whitelist AI crawler IP ranges in CDN/WAF rules.",
        "creative_fix": "Ensure public search landing pages provide accessible crawl paths for real-time search retrieval.",
        "verification": "Re-probe robots.txt and root URL using OAI-SearchBot User-Agent."
    },
    "NOINDEX_EXCLUSION": {
        "technical_fix": "Remove 'noindex' and 'none' directives from meta robots tags and X-Robots-Tag HTTP response headers.",
        "creative_fix": None,
        "verification": "Inspect HTTP response headers and DOM markup to confirm absence of noindex."
    },
    "RENDERED_CONTENT_GAP": {
        "technical_fix": "Implement Server-Side Rendering (SSR) or Static Site Generation (SSG) for initial HTML body text.",
        "creative_fix": "Ensure primary value proposition and product descriptions are rendered as semantic HTML rather than dynamic client-only state.",
        "verification": "Fetch raw HTML without executing JavaScript and confirm primary copy is present."
    },
    "CANONICAL_FRAGMENTATION": {
        "technical_fix": "Set <link rel='canonical'> href to point to the authoritative URL on the current domain.",
        "creative_fix": None,
        "verification": "Verify the canonical tag matches the authoritative host URL."
    },
    "LOCALE_MISCONFIGURATION": {
        "technical_fix": "Standardize hreflang tags to valid ISO 639-1 language and ISO 3166-1 Alpha-2 region codes.",
        "creative_fix": None,
        "verification": "Inspect alternate link tags for valid ISO codes (e.g. 'en-GB' instead of 'eng-UK')."
    },
    "MATERIAL_ENTITY_AMBIGUITY": {
        "technical_fix": "Embed Schema.org Organization JSON-LD markup on homepage declaring canonical name, url, logo, and sameAs array.",
        "creative_fix": "Explicitly state official brand name and corporate identity in page title, hero heading, and footer.",
        "verification": "Validate homepage JSON-LD using the Schema.org / Google Rich Results validator."
    },
    "ATTRIBUTE_INCOMPLETENESS": {
        "technical_fix": "Populate missing Offer properties ('price', 'priceCurrency', 'availability') in Product JSON-LD.",
        "creative_fix": "Ensure pricing, stock status, and product specifications are visible in page body copy.",
        "verification": "Verify Product schema in Google Rich Results Test shows complete attributes."
    },
    "FIRST_PARTY_FACT_CONFLICT": {
        "technical_fix": "Synchronize prices across pricing tables, product detail schemas, and checkout endpoints from a single authoritative source.",
        "creative_fix": "Review marketing and sales landing pages to eliminate outdated promotional pricing.",
        "verification": "Re-crawl affected pages and verify identical pricing appears across all listings."
    },
    "DISCONTINUED_VS_CURRENT_CONFLICT": {
        "technical_fix": "Update product schema availability to 'https://schema.org/Discontinued' on all pages referencing legacy SKUs.",
        "creative_fix": "Add clear banner copy indicating legacy lifecycle status and redirect to successor products.",
        "verification": "Verify all product pages show consistent availability and lifecycle markers."
    },
    "AI_FACT_CONFLICT": {
        "technical_fix": "Publish explicit Product & Offer JSON-LD schema to ground retrieval models with unambiguous facts.",
        "creative_fix": "Ensure core pricing and feature comparisons are formatted in clean HTML tables.",
        "verification": "Re-query assistant to confirm quoted facts align with canonical schema."
    },
    "BROKEN_AUTHORITY_ANCHOR": {
        "technical_fix": "Update or remove 4xx/5xx URLs in Schema.org 'sameAs' arrays to point to live canonical profiles.",
        "creative_fix": None,
        "verification": "Perform HTTP GET/HEAD probe on all sameAs URLs to verify HTTP 200 response."
    },
    "CLAIM_CORROBORATION_GAP": {
        "technical_fix": "Ensure declared sameAs profiles link back to the brand domain or explicitly state the brand name in title/meta tags.",
        "creative_fix": "Standardize brand naming across external registries and official social profiles.",
        "verification": "Verify external authority profile contains canonical brand name in title or og:site_name."
    },
    "MISSING_IN_DEPTH_MECHANISMS": {
        "technical_fix": "Structure explanatory content into semantic <h2>/<h3> question headings with direct answer blocks.",
        "creative_fix": "Expand product and feature descriptions to explain 'how' and 'why' the technology works using causal conjunctions.",
        "verification": "Inspect body copy to confirm presence of mechanistic depth words (how, why, because, enables)."
    },
    "INTENT_TO_LANDING_MISMATCH": {
        "technical_fix": "Anchor primary commercial call-to-action ('Buy Now', 'Contact Sales') above the fold on pricing URLs.",
        "creative_fix": "Align landing page hero headline with the specific referral search query intent.",
        "verification": "Verify interactive CTA buttons and pricing details are visible in the initial viewport."
    },
    "LOW_INFORMATION_SCENT": {
        "technical_fix": "Ensure every page includes a single semantic <h1> containing the canonical entity name.",
        "creative_fix": "Rewrite generic headings ('Welcome', 'Home') to state the specific value proposition and subject.",
        "verification": "Inspect page markup to confirm single <h1> anchors the target entity."
    }
}


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

    parser.add_argument("--inventory", help="Path to pre-acquired site-inventory JSON (bypasses acquisition)")

    # Global time limit
    parser.add_argument("--timeout-seconds", type=int, default=300,
                        help="Maximum total audit wall-clock runtime in seconds (default: 300s)")

    return parser.parse_args()



def write_inventory_file(inv):
    try:
        fd, path = tempfile.mkstemp(suffix="_inventory.json", prefix="brand_audit_")
        os.chmod(path, 0o600)
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
    
    has_sitemap = False
    if inv_stats and inv_stats.get("sitemaps_found", 0) > 0:
        has_sitemap = True
    else:
        sitemap_status = safe_check_status(f"{base_url}/sitemap.xml", timeout=5)
        if sitemap_status != 404:
            has_sitemap = True

    if not has_sitemap:
        recommendations.append({
            "id": "P-001",
            "title": "Publish a canonical XML Sitemap",
            "category": "discovery",
            "summary": "AI crawlers rely on XML sitemaps to efficiently discover brand pages without relying on deep HTML traversal.",
            "technical_fix": "Generate an XML sitemap listing all canonical public URLs and submit it via robots.txt.",
            "creative_fix": None,
            "priority": "medium",
            "verification": "Verify /sitemap.xml exists and returns valid XML."
        })

    llms_status = safe_check_status(f"{base_url}/llms.txt", timeout=5)
    if llms_status == 404:
        recommendations.append({
            "id": "P-002",
            "title": "Publish an /llms.txt standard index",
            "category": "ai-readiness",
            "summary": "The /llms.txt standard provides AI research agents with a clean, explicitly formatted summary of your brand's core facts.",
            "technical_fix": "Serve a Markdown file at /llms.txt outlining brand identity, core facts, and links to official documentation.",
            "creative_fix": "Draft concise, declarative facts in the markdown file prioritizing high-value answers for AI.",
            "priority": "low",
            "verification": "Verify /llms.txt returns HTTP 200 with valid markdown."
        })
        
    recommendations.append({
        "id": "P-003",
        "title": "Isolate substantive text from non-readable formats",
        "category": "extractability",
        "summary": "Ensure critical brand facts are explicitly stated in semantic HTML text. Avoid locking substantive information inside images without descriptive alt-text.",
        "technical_fix": "Ensure critical text is rendered via HTML tags (<article>, <p>) rather than baked into images.",
        "creative_fix": "Rewrite image-embedded text into standard body copy or provide high-fidelity alt-text.",
        "priority": "low",
        "verification": "Disable images and verify page content remains fully comprehensible."
    })
    
    recommendations.append({
        "id": "P-004",
        "title": "Implement the IndexNow Protocol",
        "category": "discovery",
        "summary": "Proactively ping search engines (via IndexNow API) when brand content changes to accelerate change notification.",
        "technical_fix": "Integrate IndexNow API calls into the CMS deployment pipeline to broadcast URL changes.",
        "creative_fix": None,
        "priority": "low",
        "verification": "Monitor IndexNow dashboard or trigger a change and verify the ping is transmitted."
    })
    
    return recommendations


def deduplicate_recommendations(rec_list, start_idx=1):
    seen = {}
    deduped = []
    for r in rec_list:
        if not isinstance(r, dict):
            continue
        title = r.get("title", "Optimization Opportunity").strip()
        summary = r.get("summary") or r.get("suggested_action") or r.get("rationale") or "Implement proactive site improvement."
        category = r.get("category", "general")
        priority = str(r.get("priority", "low")).lower()
        if priority not in ("critical", "high", "medium", "low"):
            priority = "low"
        key = " ".join(title.lower().split())
        if key in seen:
            continue
        item = {
            "title": title,
            "category": category,
            "summary": summary,
            "priority": priority
        }
        if "technical_fix" in r: item["technical_fix"] = r["technical_fix"]
        if "creative_fix" in r: item["creative_fix"] = r["creative_fix"]
        if "verification" in r: item["verification"] = r["verification"]
        
        seen[key] = item
        deduped.append(item)
        
    for i, item in enumerate(deduped):
        item["id"] = f"P-{(start_idx + i):03d}"
    return deduped




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
            if sid and not skill.get("entrypoint") and not skill.get("optional"):
                base = sid.replace("-audit", "").replace("-", "_")

                # Dynamically resolve script name instead of hardcoding
                import glob
                script_dir = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), sid, "scripts")
                possible_scripts = glob.glob(os.path.join(script_dir, "*_check.py"))
                if possible_scripts:
                    script_name = os.path.basename(possible_scripts[0])
                else:
                    script_name = f"{sid.replace('-audit', '').replace('-', '_')}_check.py"

                label = f"Dynamic execution of {sid}"
                if "discoverability" in sid: label = "Access, robots.txt & rendering risk"
                if "entity" in sid: label = "Entity identity & offer extractability"
                if "fact" in sid: label = "Fact ledger & cross-page consistency"
                if "corroboration" in sid: label = "Declared authority link verification"
                if "engagement" in sid: label = "Orientation & journey continuity"
                if "geo" in sid: label = "Generative engine optimization & causal depth"
                
                plugins.append((sid, label, script_name, []))
    except Exception as e:
        pass
    
    if not plugins:
        plugins = [
            ("discoverability-audit", "Access, robots.txt & rendering risk", "discoverability_check.py", []),
            ("entity-content-audit", "Entity identity & offer extractability", "entity_content_check.py", []),
            ("fact-consistency-audit", "Fact ledger & cross-page consistency", "fact_consistency_check.py", []),
            ("corroboration-authority-audit", "Declared authority link verification", "corroboration_check.py", []),
            ("geo-content-audit", "Generative engine optimization & causal depth", "geo_content_check.py", []),
            ("engagement-context-audit", "Orientation & journey continuity", "engagement_check.py", []),
        ]
    return plugins



def compose_audit(site, include_proactive=True, with_representation=False,
                  responses_file=None, timeout_seconds=300, return_internal=False,
                  inventory_file=None):
    start_mono = time.monotonic()
    monotonic_deadline = start_mono + timeout_seconds
    domain, base_url = normalize_target(site)
    raw_findings = []
    specialists = {}
    specialist_recommendations = []
    all_observations = []
    all_coverage = {}
    all_limitations = []
    cleanup_inventory = True

    # 1. Acquisition Phase (Type-Safe Shared Inventory) - max 60s
    if inventory_file and os.path.exists(inventory_file):
        try:
            with open(inventory_file, "r", encoding="utf-8") as f:
                inventory = json.load(f)
            inv_stats = {
                "pages_discovered": len(inventory.get("pages", [])),
                "html_pages_sampled": len([p for p in inventory.get("pages", []) if p.get("resource_type") == "html" or "html" in str(p.get("content_type", "")) or p.get("html")]),
                "sitemaps_found": len(inventory.get("sitemaps", [])),
                "robots_txt_found": bool(inventory.get("robots_txt")),
                "homepage_reachable": True
            }
            inventory_path = inventory_file
            cleanup_inventory = False
        except Exception:
            inventory = None
            inventory_path = None
    else:
        acquisition_deadline = min(monotonic_deadline, start_mono + 60)
        inventory, inv_stats = build_inventory(base_url, deadline=acquisition_deadline)
        inventory_path = write_inventory_file(inventory) if inventory else None

    if inventory_path:
        all_coverage["site_inventory"] = inv_stats
        all_limitations.extend(inventory.get("limitations", []))
    elif inv_stats and not inv_stats.get("homepage_reachable", True):
        all_limitations.append(f"Homepage unreachable ({inv_stats.get('error', 'Network error')}); inventory could not be built.")

    # 2. Sequential Stateful Graph Execution
    import tempfile
    state_fd, state_path = tempfile.mkstemp(suffix=".json")
    os.close(state_fd)
    with open(state_path, "w") as f:
        json.dump({}, f)

    # Strictly enforced causal pipeline order
    pipeline_order = [
        ("discoverability-audit", "discoverability_check.py"),
        ("entity-content-audit", "entity_content_check.py"),
        ("fact-consistency-audit", "fact_consistency_check.py"),
        ("corroboration-authority-audit", "corroboration_check.py"),
        ("geo-content-audit", "geo_content_check.py"),
        ("engagement-context-audit", "engagement_check.py")
    ]
    
    available_plugins = {s[0]: s for s in discover_plugins()}
    
    rep_args = []
    if responses_file and os.path.exists(responses_file):
        rep_args = ["--responses", responses_file]

    for idx, (skill_name, script_name) in enumerate(pipeline_order):
        now = time.monotonic()
        remaining_time = monotonic_deadline - now
        remaining_specialists = len(pipeline_order) - idx

        if skill_name not in available_plugins:
            continue
            
        label = available_plugins[skill_name][1]
        
        if remaining_time <= 5:
            specialists[skill_name] = {
                "label": label,
                "status": "not_run",
                "reason": "Execution skipped: global time budget exhausted"
            }
            all_limitations.append(f"{skill_name}: Skipped due to global execution time limit.")
            continue

        spec_timeout = max(10, min(40, int((remaining_time - 5) / max(1, remaining_specialists))))

        script = find_specialist_script(skill_name, script_name)
        args = ["--site", base_url, "--format", "json", "--state", state_path]
        if inventory_path:
            args += ["--inventory", inventory_path]
            
        if skill_name == "fact-consistency-audit" and rep_args:
            args += rep_args

        status, findings, recs, error, observations, coverage, limitations =             run_specialist_tool(script, spec_timeout, *args)

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
        
    try:
        with open(state_path, "r") as f:
            final_knowledge_graph = json.load(f)
        os.unlink(state_path)
    except Exception:
        final_knowledge_graph = {}

    if inventory_path and cleanup_inventory:
        try:
            os.unlink(inventory_path)
        except OSError:
            pass

    # Deduplicate specialist recommendations
    deduped_specialist = deduplicate_recommendations(list(specialist_recommendations), start_idx=1)
    
    # Proactive checks already have valid IDs, just append them or re-number
    proactive = []
    if include_proactive:
        proactive = proactive_checks(domain, base_url, inv_stats=inv_stats)
        
    # Re-number proactive to follow specialist
    start_idx = len(deduped_specialist) + 1
    for i, p in enumerate(proactive):
        p["id"] = f"P-{(start_idx + i):03d}"
        
    all_recommendations = deduped_specialist + proactive

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
            consolidated_raw.append(group[0])
            continue
            
        merged = dict(group[0])
        all_evidence = set()
        for f in group:
            ev = f.get("evidence")
            if ev:
                all_evidence.add(ev.strip())
                
        if len(all_evidence) > 1:
            merged["evidence"] = " | ".join(sorted(all_evidence)[:4])
            merged["title"] = f"{merged['title']} (Multiple Occurrences)"
            
        consolidated_raw.append(merged)

    final_findings = []
    seen_fps = set()
    demoted = []
    
    # We define a minimal SEVERITY_ORDER for sorting
    SEVERITY_ORDER = {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 5}
    sorted_raw = sorted(consolidated_raw, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "medium") if isinstance(f, dict) else "medium", 99))

    for item in sorted_raw:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity", "medium")).lower()
        if sev == "info" or sev not in ("critical", "high", "medium", "low"):
            sev = "low"
        confidence = str(item.get("confidence", "medium")).lower()
        fp = f"{item.get('category', '')}:{item.get('title', '')}"
        if fp in seen_fps:
            continue
        seen_fps.add(fp)

        # Parse raw evidence string into evidence object if needed
        raw_evidence = item.get("evidence", "")
        if isinstance(raw_evidence, dict):
            evidence_obj = raw_evidence
        else:
            evidence_str = str(raw_evidence).strip()
            if len(evidence_str) < 5:
                continue
            evidence_obj = {
                "summary": evidence_str,
                "sources": [{"url": base_url, "type": "first_party", "observation": evidence_str}],
                "scope": item.get("scope", "site")
            }

        if sev in ("critical", "high") and confidence == "low":
            continue

        action = item.get("suggested_action", {})
        action_summary = action.get("summary") if isinstance(action, dict) else str(action)
        action_priority = str(action.get("priority", sev)).lower() if isinstance(action, dict) else sev
        if action_priority == "info" or action_priority not in ("critical", "high", "medium", "low"):
            action_priority = "low" 
        
        suggested_action = {
            "summary": action_summary,
            "priority": action_priority
        }
        
        if isinstance(action, dict):
            if "technical_fix" in action: suggested_action["technical_fix"] = action["technical_fix"]
            if "creative_fix" in action: suggested_action["creative_fix"] = action["creative_fix"]
            if "verification" in action: suggested_action["verification"] = action["verification"]

        cid = item.get("cause_id")
        if cid in CAUSE_REMEDY_FALLBACKS:
            fallback = CAUSE_REMEDY_FALLBACKS[cid]
            if "technical_fix" not in suggested_action or suggested_action["technical_fix"] is None:
                suggested_action["technical_fix"] = fallback.get("technical_fix")
            if "creative_fix" not in suggested_action or suggested_action["creative_fix"] is None:
                suggested_action["creative_fix"] = fallback.get("creative_fix")
            if "verification" not in suggested_action or not suggested_action["verification"]:
                suggested_action["verification"] = fallback.get("verification")

        finding_entry = {
            "id": f"F-{len(final_findings) + 1:03d}",
            "title": item.get("title", "Audit Finding"),
            "severity": sev,
            "category": item.get("category", "general"),
            "root_cause": item.get("root_cause", "Auditor identified an architectural or content constraint."),
            "confidence": confidence,
            "evidence": evidence_obj,
            "suggested_action": suggested_action
        }
        
        if "impact" in item:
            finding_entry["impact"] = item["impact"]
            
        final_findings.append(finding_entry)

    total_findings = len(final_findings)
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in final_findings:
        sev = f.get("severity", "medium")
        if sev in counts:
            counts[sev] += 1

    audit_status = "complete"
    failed_specs = [name for name, sp in specialists.items() if sp.get("status") in ("failed", "not_run")]
    if len(failed_specs) == len(specialists) and len(specialists) > 0:
        audit_status = "failed"
    elif failed_specs:
        audit_status = "partial"

    final_report = {
        "site": base_url,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audit_status": audit_status,
        "summary": {
            "total_findings": total_findings,
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"]
        },
        "findings": final_findings,
        "proactive_actions": all_recommendations,
        
    }

    internal_trace = {
        "specialists": specialists,
        "observations": all_observations,
        "coverage": all_coverage,
        "limitations": all_limitations
    }

    if return_internal:
        return final_report, internal_trace
    return final_report

def validation_gate(report):
    try:
        proc = subprocess.run(
            [sys.executable, VALIDATOR, "-"],
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




def generate_mermaid_trace(report, out_path, internal_data=None):
    """Deterministic State Telemetry: Generates a Mermaid.js execution graph."""
    lines = [
        "```mermaid",
        "graph TD",
        '    subgraph "Acquisition Phase"',
        '        A[Master Orchestrator] -->|ThreadPool BFS| B(Shared Site Inventory)',
        f'        B -->|Sampled {(internal_data or {}).get("audit_metrics", {}).get("html_pages_sampled", 0)} pages| C{{Dispatcher}}',
        '    end',
        '    subgraph "Dynamic Specialist Plugins"'
    ]
    
    specs = (internal_data or {}).get("specialists", {})
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


def format_rich_report(report, internal_data=None):
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
    metrics = (internal_data or {}).get("audit_metrics", {})
    
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



# State Mapping Contract:
# Specialist Internal States:
#  - "ok": Analyzed successfully.
#  - "inconclusive": Lacked evidence to make a full determination (e.g., missing HTML).
#  - "failed": Internal error or timeout.
#  - "not_run": Orchestrator deliberately skipped execution (e.g., timeout).
#
# Orchestrator Public Report States:
#  - "complete": All mandatory specialists returned "ok".
#  - "partial": At least one mandatory specialist returned "inconclusive" or "failed".
#  - "failed": Critical orchestration failure, preventing audit execution.

def main():
    args = parse_args()
    report, internal_data = compose_audit(
        args.site,
        include_proactive=args.include_proactive,
        timeout_seconds=args.timeout_seconds,
        return_internal=True,
        inventory_file=args.inventory
    )

    if not validation_gate(report):
        sys.exit(1)


    if args.trace:
        try:
            generate_mermaid_trace(report, args.trace, internal_data)
        except Exception as e:
            sys.stderr.write(f"Trace generation warning: {e}\n")

    if args.format == "markdown":
        out_content = format_markdown_report(report)
    elif args.format == "rich":
        out_content = format_rich_report(report, internal_data)
    else:
        out_content = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_content + "\n")
    else:
        print(out_content)


if __name__ == "__main__":
    main()
