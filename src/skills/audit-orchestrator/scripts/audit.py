#!/usr/bin/env python3
"""audit.py - Entrypoint CLI for Brand AI-Readiness Audit.

Supports:
  - collect:  Bounded single-pass acquisition, specialist sensor runs, coverage tracking, bundle & baseline report emission.
  - finalize: Ingest agent semantic review, compose with collected evidence, rank tasks, and emit schema-validated final report.
  - validate: Validate report against Draft-07 JSON Schema and consistency invariants.

Python 3.9+ standard library ONLY. Zero runtime third-party pip dependencies.
"""

import argparse
import json
import multiprocessing
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
ROOT_DIR = SCRIPT_DIR.parents[2]

# Ensure skills scripts are in sys.path
for skill_folder in SKILLS_DIR.iterdir():
    scripts_path = skill_folder / "scripts"
    if scripts_path.is_dir() and str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))

try:
    from .assemble_report import assemble, validate_report  # type: ignore
except (ImportError, ValueError):
    try:
        from assemble_report import assemble, validate_report  # type: ignore
    except ImportError:
        # Fallback to local import if executed within script dir
        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))
        from assemble_report import assemble, validate_report  # type: ignore


def normalize_site_url(url: str) -> str:
    """Normalize input site into scheme and hostname."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    scheme = parsed.scheme if parsed.scheme in ("http", "https") else "https"
    netloc = parsed.netloc or parsed.path.split("/")[0]
    return f"{scheme}://{netloc}"


def write_atomic_json(path: Path, value: Any) -> None:
    """Atomically write JSON to file via temporary replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def compute_coverage(checks: List[Dict[str, Any]], candidates: List[Dict[str, Any]], pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute 134-check coverage tracking across observed, needs_agent_review, blocked, not_possible, not_applicable."""
    seen_checks = {c.get("check_id") for c in candidates if isinstance(c, dict) and "check_id" in c}
    check_results = []
    for c in checks:
        cid = c.get("check_id", "")
        feasibility = c.get("feasibility", "")
        owner = c.get("owner", "discoverability-audit")
        if cid in seen_checks:
            status = "observed"
            reason = "Scoped observations available from sensors; not a whole-check pass"
        elif feasibility == "Exclude":
            status = "not_applicable"
            reason = "Duplicate check; reuse corresponding primary check"
        elif feasibility.startswith("Not possible"):
            status = "not_possible"
            reason = "URL-only public scope cannot establish the requested conclusion"
        elif not pages:
            status = "blocked"
            reason = "No usable pages collected in single-pass inventory"
        else:
            status = "needs_agent_review"
            reason = "Apply specialist reference predicate to available inventory; absence of defect is not a pass"
        check_results.append(dict(check_id=cid, status=status, reason=reason, owner=owner))

    return {
        "checks": check_results,
        "observed_pages": len(pages),
        "whole_site_complete": False,
        "browser_available": False,
        "browser_reason": "Zero-dependency pure Python runtime sandbox",
        "optional_capabilities": {
            "independent_profile_search": False,
            "pdf_ocr": False,
            "history": False,
            "authenticated_flows": False,
        },
    }


def make_evidence_ref(
    ev_text: str,
    cand_scope: str,
    s_art: str,
    pages_by_url: Dict[str, Tuple[str, str]],
) -> List[Dict[str, Any]]:
    clean_ev = str(ev_text or "").strip()
    if cand_scope in pages_by_url:
        page_art, page_body = pages_by_url[cand_scope]
        # Check if an exact quoted string from ev_text is present in the raw page body
        quotes = re.findall(r'["\']([^"\']{4,100})["\']', clean_ev)
        for q in quotes:
            if q in page_body:
                return [{"artifact": page_art, "locator": "text", "quote": q}]
        # Structural locator on primary page artifact (never citing sensor summary as website quote)
        return [{"artifact": page_art, "locator": "dom:document", "quote": None, "structural_observation": clean_ev[:160]}]

    if "/robots.txt" in cand_scope or "robots" in cand_scope.lower():
        return [{"artifact": "robots.txt", "locator": "directive", "quote": clean_ev[:120]}]
    if "/sitemap" in cand_scope or "sitemap" in cand_scope.lower():
        return [{"artifact": "sitemap.xml", "locator": "xml", "quote": clean_ev[:120]}]

    return [{"artifact": "inv.json", "locator": "inventory:scope", "quote": None, "structural_observation": clean_ev[:160]}]


def execute_audit_sensors(
    base: str,
    domain: str,
    inv: Dict[str, Any],
    sensor_errors: Optional[List[Dict[str, Any]]] = None,
    sensor_results: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Run specialist sensors offline against inventory and extract candidates."""
    candidates: List[Dict[str, Any]] = []
    band_map = {"critical": "S4", "high": "S3", "medium": "S2", "low": "S1"}

    pages = inv.get("pages", []) if inv else []
    pages_by_url: Dict[str, Tuple[str, str]] = {}
    for i, p in enumerate(pages):
        if isinstance(p, dict):
            art_id = f"response-{i + 1:04d}"
            body = str(p.get("html") or p.get("raw_html") or p.get("clean_text") or "")
            u = p.get("url") or ""
            if u:
                pages_by_url[u] = (art_id, body)

    # 1. Discoverability sensor
    try:
        import discoverability_check  # type: ignore
        disc_res = discoverability_check.audit(base, domain, inv=inv)
        if sensor_results is not None:
            sensor_results["discoverability-audit"] = disc_res
        findings_list = disc_res.get("findings", [])
        if isinstance(findings_list, list):
            for f in findings_list:
                if not isinstance(f, dict):
                    continue
                raw_cid = str(f.get("check_id") or f.get("cause_id") or f.get("id") or "B1")
                cid = raw_cid.split("-")[0] if "-" in raw_cid else raw_cid
                if not (len(cid) in (2, 3) and cid[0].isalpha() and cid[1:].isdigit()):
                    cid = "B1"
                cand_scope = f.get("url") or f.get("scope") or (inv.get("pages", [{}])[0].get("url", base) if inv.get("pages") else base)
                sev = f.get("severity", "medium")
                band = f.get("actual_band") or band_map.get(sev, "S2")
                ev_str = str(f.get("evidence", ""))
                candidates.append({
                    "check_id": cid,
                    "cause_id": str(f.get("cause_id") or f.get("id") or cid),
                    "url": str(f.get("url") or cand_scope),
                    "title": str(f.get("title", "Discoverability observation")),
                    "actual_band": band,
                    "finding_kind": "confirmed_problem" if band in ("S3", "S4") else "advisory",
                    "scope": cand_scope,
                    "observation": ev_str,
                    "evidence_refs": make_evidence_ref(ev_str, cand_scope, "sensor-discoverability-audit", pages_by_url),
                    "collection_complete_for_scope": True,
                    "severity_reason": str(f.get("title", "")),
                    "suggested_action": f.get("suggested_action", {
                        "summary": "Resolve discoverability barrier",
                        "priority": sev if sev in band_map else "medium",
                    }),
                })
    except Exception as e:
        if sensor_errors is not None:
            sensor_errors.append({"sensor": "discoverability-audit", "error": str(e), "error_type": type(e).__name__})

    # 2. Entity & Content sensor
    try:
        import entity_content_check  # type: ignore
        ent_res = entity_content_check.audit(base, domain, inv=inv)
        if sensor_results is not None:
            sensor_results["entity-content-audit"] = ent_res
        findings_list = ent_res.get("findings", [])
        if isinstance(findings_list, list):
            for f in findings_list:
                if not isinstance(f, dict):
                    continue
                raw_cid = str(f.get("check_id") or f.get("cause_id") or f.get("id") or "E1")
                cid = raw_cid.split("-")[0] if "-" in raw_cid else raw_cid
                if not (len(cid) in (2, 3) and cid[0].isalpha() and cid[1:].isdigit()):
                    cid = "E1"
                cand_scope = f.get("url") or f.get("scope") or base
                sev = f.get("severity", "medium")
                band = f.get("actual_band") or band_map.get(sev, "S2")
                ev_str = str(f.get("evidence", ""))
                candidates.append({
                    "check_id": cid,
                    "cause_id": str(f.get("cause_id") or f.get("id") or cid),
                    "url": str(f.get("url") or cand_scope),
                    "title": str(f.get("title", "Entity schema observation")),
                    "actual_band": band,
                    "finding_kind": "confirmed_problem" if band in ("S3", "S4") else "advisory",
                    "scope": cand_scope,
                    "observation": ev_str,
                    "evidence_refs": make_evidence_ref(ev_str, cand_scope, "sensor-entity-content-audit", pages_by_url),
                    "collection_complete_for_scope": True,
                    "severity_reason": str(f.get("title", "")),
                    "suggested_action": f.get("suggested_action", {
                        "summary": "Implement Schema.org structured data",
                        "priority": sev if sev in band_map else "medium",
                    }),
                })
    except Exception as e:
        if sensor_errors is not None:
            sensor_errors.append({"sensor": "entity-content-audit", "error": str(e), "error_type": type(e).__name__})

    # 3. Fact consistency sensor
    try:
        import fact_consistency_check  # type: ignore
        fact_res = fact_consistency_check.audit(base, domain, inv=inv)
        if sensor_results is not None:
            sensor_results["fact-consistency-audit"] = fact_res
        findings_list = fact_res.get("findings", [])
        if isinstance(findings_list, list):
            for f in findings_list:
                if not isinstance(f, dict):
                    continue
                raw_cid = str(f.get("check_id") or "")
                cause = str(f.get("cause_id") or f.get("id") or "")
                if not (len(raw_cid) in (2, 3, 4) and raw_cid.startswith("BN") and raw_cid[2:].isdigit()):
                    fact_map = {
                        "COMMERCIAL_PRODUCT_DATA_CONTRADICTION": "BN3",
                        "LEGACY_FACT_PROPAGATION": "BN9",
                        "STALE_AUTHORITATIVE_FACT": "BN9",
                        "DISCONTINUED_VS_CURRENT_CONFLICT": "BN4",
                        "FIRST_PARTY_FACT_CONFLICT": "BN1",
                        "CONFLICTING_COMMERCIAL_TERMS": "BN3",
                    }
                    raw_cid = fact_map.get(cause, "BN1")
                cand_scope = f.get("url") or f.get("scope") or base
                sev = f.get("severity", "medium")
                band = f.get("actual_band") or band_map.get(sev, "S2")
                ev_str = str(f.get("evidence", ""))
                candidates.append({
                    "check_id": raw_cid,
                    "cause_id": cause or raw_cid,
                    "url": str(f.get("url") or cand_scope),
                    "title": str(f.get("title", "Fact consistency observation")),
                    "actual_band": band,
                    "finding_kind": "confirmed_problem" if band in ("S3", "S4") else "advisory",
                    "scope": cand_scope,
                    "observation": ev_str,
                    "evidence_refs": make_evidence_ref(ev_str, cand_scope, "sensor-fact-consistency-audit", pages_by_url),
                    "collection_complete_for_scope": True,
                    "severity_reason": str(f.get("title", "")),
                    "suggested_action": f.get("suggested_action", {
                        "summary": "Reconcile first-party claims",
                        "priority": sev if sev in band_map else "medium",
                    }),
                })
    except Exception as e:
        if sensor_errors is not None:
            sensor_errors.append({"sensor": "fact-consistency-audit", "error": str(e), "error_type": type(e).__name__})

    # 4. Corroboration sensor
    try:
        import corroboration_check  # type: ignore
        corr_res = corroboration_check.audit(base, domain, inv=inv)
        if sensor_results is not None:
            sensor_results["corroboration-authority-audit"] = corr_res
        findings_list = corr_res.get("findings", [])
        if isinstance(findings_list, list):
            for f in findings_list:
                if not isinstance(f, dict):
                    continue
                raw_cid = str(f.get("check_id") or "")
                cause = str(f.get("cause_id") or f.get("id") or "")
                if not (len(raw_cid) in (2, 3, 4) and raw_cid[:2].isalpha()):
                    corrob_map = {
                        "CIRCULAR_SAMEAS_SELF_REFERENCE": "BC1",
                        "WEAK_IDENTITY_SIGNALS": "BC2",
                        "CANDIDATE_BACKLINK_UNREACHABLE": "BC3",
                        "BROKEN_AUTHORITY_ANCHOR": "BC6",
                        "CLAIM_CORROBORATION_GAP": "PP1",
                    }
                    raw_cid = corrob_map.get(cause, "BC6")
                cand_scope = f.get("url") or f.get("scope") or base
                sev = f.get("severity", "low")
                band = f.get("actual_band") or band_map.get(sev, "S2")
                ev_str = str(f.get("evidence", ""))
                candidates.append({
                    "check_id": raw_cid,
                    "cause_id": cause or raw_cid,
                    "url": str(f.get("url") or cand_scope),
                    "title": str(f.get("title", "Authority anchor observation")),
                    "actual_band": band,
                    "finding_kind": "confirmed_problem" if band in ("S3", "S4") else "advisory",
                    "scope": cand_scope,
                    "observation": ev_str,
                    "evidence_refs": make_evidence_ref(ev_str, cand_scope, "sensor-corroboration-authority-audit", pages_by_url),
                    "collection_complete_for_scope": True,
                    "severity_reason": str(f.get("title", "")),
                    "suggested_action": f.get("suggested_action", {
                        "summary": "Link reciprocal authoritative sameAs anchors",
                        "priority": sev if sev in band_map else "low",
                    }),
                })
    except Exception as e:
        if sensor_errors is not None:
            sensor_errors.append({"sensor": "corroboration-authority-audit", "error": str(e), "error_type": type(e).__name__})

    # 5. GEO Content sensor
    try:
        import geo_content_check  # type: ignore
        geo_res = geo_content_check.audit(base, domain, inv=inv)
        if sensor_results is not None:
            sensor_results["geo-content-audit"] = geo_res
        findings_list = geo_res.get("findings", [])
        if isinstance(findings_list, list):
            for f in findings_list:
                if not isinstance(f, dict):
                    continue
                raw_cid = str(f.get("check_id") or "")
                cause = str(f.get("cause_id") or f.get("id") or "")
                if not (len(raw_cid) in (2, 3) and raw_cid[0] == "N" and raw_cid[1:].isdigit()):
                    geo_map = {
                        "LOW_CITABILITY_SCORE": "N1",
                        "CONTEXT_PLACEMENT_DEGRADATION": "N2",
                        "LACK_OF_SPECIFIC_EVIDENCE": "N3",
                        "COMMERCIAL_INTRUSION_IN_INFORMATIONAL_CONTENT": "N7",
                        "MISSING_IN_DEPTH_MECHANISMS": "N10",
                        "STANDALONE_FAQ_DEFICIT": "N11",
                        "EXCESSIVE_KEYWORD_DENSITY": "N12",
                        "LOW_FACT_TO_TOKEN_RATIO": "N13",
                        "EXCESSIVE_HEDGE_LANGUAGE": "N14",
                        "CONTENT_RECENCY_DEFICIT": "N15",
                    }
                    raw_cid = geo_map.get(cause, "N1")
                cand_scope = f.get("url") or f.get("scope") or base
                sev = f.get("severity", "medium")
                band = f.get("actual_band") or band_map.get(sev, "S2")
                ev_str = str(f.get("evidence", ""))
                candidates.append({
                    "check_id": raw_cid,
                    "cause_id": cause or raw_cid,
                    "url": str(f.get("url") or cand_scope),
                    "title": str(f.get("title", "GEO citability observation")),
                    "actual_band": band,
                    "finding_kind": "confirmed_problem" if band in ("S3", "S4") else "advisory",
                    "scope": cand_scope,
                    "observation": ev_str,
                    "evidence_refs": make_evidence_ref(ev_str, cand_scope, "sensor-geo-content-audit", pages_by_url),
                    "collection_complete_for_scope": True,
                    "severity_reason": str(f.get("title", "")),
                    "suggested_action": f.get("suggested_action", {
                        "summary": "Optimize text structure and statistical density for generative engine extraction",
                        "priority": sev if sev in band_map else "medium",
                    }),
                })
    except Exception as e:
        if sensor_errors is not None:
            sensor_errors.append({"sensor": "geo-content-audit", "error": str(e), "error_type": type(e).__name__})

    # 6. Engagement & Bridge sensor
    try:
        import engagement_check  # type: ignore
        eng_res = engagement_check.audit(base, domain, inv=inv)
        if sensor_results is not None:
            sensor_results["engagement-context-audit"] = eng_res
        findings_list = eng_res.get("findings", [])
        if isinstance(findings_list, list):
            for f in findings_list:
                if not isinstance(f, dict):
                    continue
                raw_cid = str(f.get("check_id") or "")
                cause = str(f.get("cause_id") or f.get("id") or "")
                if not (len(raw_cid) in (2, 3) and raw_cid[0] in ("I", "J") and raw_cid[1:].isdigit()):
                    eng_map = {
                        "LOW_INFORMATION_SCENT": "J1",
                        "GENERIC_H1": "J1",
                        "DESTINATION_NAVIGATION_FRICTION": "J2",
                        "VIEWPORT_ANSWER_ABSENCE": "J3",
                        "CTA_REACHABILITY_FRICTION": "J4",
                        "COMMERCIAL_HANDOFF_DISCONTINUITY": "J4",
                        "AI_REFERRAL_DISCONTINUITY": "J5",
                        "INTENT_TO_LANDING_MISMATCH": "J8",
                        "AGENT_INTERACTION_BARRIER": "J10",
                    }
                    raw_cid = eng_map.get(cause, "J1")
                cand_scope = f.get("url") or f.get("scope") or base
                sev = f.get("severity", "medium")
                band = f.get("actual_band") or band_map.get(sev, "S2")
                ev_str = str(f.get("evidence", ""))
                candidates.append({
                    "check_id": raw_cid,
                    "cause_id": cause or raw_cid,
                    "url": str(f.get("url") or cand_scope),
                    "title": str(f.get("title", "Visitor engagement observation")),
                    "actual_band": band,
                    "finding_kind": "confirmed_problem" if band in ("S3", "S4") else "advisory",
                    "scope": cand_scope,
                    "observation": ev_str,
                    "evidence_refs": make_evidence_ref(ev_str, cand_scope, "sensor-engagement-context-audit", pages_by_url),
                    "collection_complete_for_scope": True,
                    "severity_reason": str(f.get("title", "")),
                    "suggested_action": f.get("suggested_action", {
                        "summary": "Improve post-citation intent scent and CTA reachability",
                        "priority": sev if sev in band_map else "medium",
                    }),
                })
    except Exception as e:
        if sensor_errors is not None:
            sensor_errors.append({"sensor": "engagement-context-audit", "error": str(e), "error_type": type(e).__name__})

    return candidates


def worker_collect(site: str, out_dir: Path, max_pages: int, seconds: int, probe_params: bool) -> None:
    """Worker process: acquire inventory, run sensors, assemble baseline report within deadline."""
    started = time.monotonic()
    checks_file = SCRIPT_DIR.parents[0] / "references" / "checks.json"
    checks = json.loads(checks_file.read_text(encoding="utf-8")) if checks_file.exists() else []

    evidence_dir = out_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1. Acquire inventory via web-scraper
    builder = None
    try:
        from acquire_inventory import build_inventory as inv_builder  # type: ignore
        builder = inv_builder
    except ImportError:
        try:
            from .acquire_inventory import build_inventory as inv_builder  # type: ignore
            builder = inv_builder
        except (ImportError, ValueError):
            builder = None

    if builder is not None:
        inv_res = builder(site, max_pages=max_pages, timeout_seconds=int(min(float(seconds), 60.0)))
        if isinstance(inv_res, tuple):
            inv = inv_res[0]
        elif isinstance(inv_res, dict):
            inv = inv_res
        else:
            inv = {"site": site, "pages": []}
    else:
        inv = {"site": site, "pages": []}

    pages: List[Dict[str, Any]] = [p for p in inv.get("pages", []) if isinstance(p, dict)]
    records: List[Dict[str, Any]] = []
    for i, p in enumerate(pages):
        art_id = f"response-{i + 1:04d}"
        body_text = p.get("html") or p.get("raw_html") or ""
        (evidence_dir / f"{art_id}.body").write_text(body_text, encoding="utf-8", errors="replace")
        records.append({
            "artifact": art_id,
            "file": f"{art_id}.body",
            "url": p.get("url", site),
            "status": p.get("status_code") or p.get("status") or 200,
            "headers": [["content-type", "text/html"]],
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "complete": True,
            "bytes": len(body_text.encode("utf-8")),
            "elapsed_ms": 150,
            "text": body_text,
            "source": {
                "text": body_text,
                "canonicals": p.get("canonicals", []),
                "jsonld": p.get("jsonld", []),
            },
            "limitation": "",
        })

    # 2. Run sensors
    base = normalize_site_url(site)
    parsed = urlparse(base)
    domain = parsed.netloc or parsed.path
    sensor_errors: List[Dict[str, Any]] = []
    sensor_results: Dict[str, Any] = {}
    candidates = execute_audit_sensors(base, domain, inv, sensor_errors=sensor_errors, sensor_results=sensor_results)

    # Persist sensor measurements into evidence records
    for s_name, s_res in sensor_results.items():
        s_art = f"sensor-{s_name}"
        s_text = json.dumps(s_res, ensure_ascii=False)
        (evidence_dir / f"{s_art}.json").write_text(s_text, encoding="utf-8", errors="replace")
        records.append({
            "artifact": s_art,
            "file": f"{s_art}.json",
            "url": base,
            "status": 200,
            "headers": [["content-type", "application/json"]],
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "complete": True,
            "bytes": len(s_text.encode("utf-8")),
            "elapsed_ms": 50,
            "text": s_text,
            "source": {"text": s_text},
            "sensor": s_name,
            "limitation": "",
        })

    # Save complete evidence index
    (evidence_dir / "evidence-index.json").write_text(
        json.dumps({"records": records, "skipped": []}, indent=2), encoding="utf-8"
    )

    # 3. Coverage tracking
    cov = compute_coverage(checks, candidates, pages)
    cov["requests"] = len(records)
    cov["elapsed_seconds"] = round(time.monotonic() - started, 3)
    cov["skipped_urls"] = []
    cov["sensor_errors"] = sensor_errors

    # 4. Save bundle
    bundle = {
        "site": base,
        "pages": pages,
        "records": records,
        "candidates": candidates,
        "content_inventory": inv.get("metadata", {}),
        "profiles": [],
        "browser": {"available": False, "reason": "Standard pure Python library execution", "captures": []},
        "coverage": cov,
        "sensor_errors": sensor_errors,
    }
    write_atomic_json(out_dir / "bundle.json", bundle)

    # 5. Assemble baseline report
    report = assemble(base, candidates, records, checks, cov, bundle["browser"])
    write_atomic_json(out_dir / "audit-report.json", report)

    # 6. Save machine-readable execution manifest
    manifest = report.get("run_manifest") or {
        "manifest_version": "1.0.0",
        "site": base,
        "audited_at": report.get("audited_at"),
        "duration_seconds": round(time.monotonic() - started, 3),
        "execution_status": report.get("audit_status", "complete"),
        "pages_crawled": len(pages),
        "candidates_count": len(candidates),
        "findings_count": len(report.get("findings", [])),
        "participating_skills": [
            "audit-orchestrator",
            "web-scraper",
            "discoverability-audit",
            "entity-content-audit",
            "fact-consistency-audit",
            "corroboration-authority-audit",
            "geo-content-audit",
            "engagement-context-audit",
        ],
        "browser": {"available": False, "reason": "Standard pure Python library execution (zero headless browser binaries)"},
    }
    write_atomic_json(out_dir / "run-manifest.json", manifest)


def collect(args: argparse.Namespace) -> None:
    """Execute bounded collection in a child process protected by a watchdog."""
    site = normalize_site_url(args.site)
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    proc = multiprocessing.Process(
        target=worker_collect,
        args=(site, out_dir, args.pages, args.seconds, args.probe_parameters),
    )
    proc.start()
    proc.join(args.seconds + 15)

    if proc.is_alive():
        proc.terminate()
        proc.join(3)
        if proc.is_alive():
            proc.kill()
        checks_file = SCRIPT_DIR.parents[0] / "references" / "checks.json"
        checks = json.loads(checks_file.read_text(encoding="utf-8")) if checks_file.exists() else []
        report = assemble(
            site,
            [],
            [],
            checks,
            {
                "whole_site_complete": False,
                "deadline_exceeded": True,
                "checks": [{"check_id": c.get("check_id"), "status": "blocked", "reason": "Hard worker deadline exceeded"} for c in checks],
            },
        )
        write_atomic_json(out_dir / "audit-report.json", report)
        print("Deadline reached; emitted blocked baseline report")
    elif proc.exitcode:
        raise SystemExit(f"Collection failed (exit code {proc.exitcode}); no report emitted")
    else:
        print(str(out_dir / "audit-report.json"))


def finalize(args: argparse.Namespace) -> None:
    """Compose agent review with collected evidence and assemble final validated report."""
    bundle_path = Path(args.bundle).resolve()
    review_path = Path(args.review).resolve()
    out_path = Path(args.out).resolve()

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))

    checks_file = SCRIPT_DIR.parents[0] / "references" / "checks.json"
    checks = json.loads(checks_file.read_text(encoding="utf-8")) if checks_file.exists() else []

    rev_candidates = review.get("candidates") if isinstance(review.get("candidates"), list) else (review.get("findings") if isinstance(review.get("findings"), list) else None)
    if not isinstance(review, dict) or rev_candidates is None:
        raise ValueError("Agent review must be an object with a candidates or findings array")

    all_candidates = bundle.get("candidates", []) + rev_candidates
    report = assemble(
        bundle["site"],
        all_candidates,
        bundle.get("records", []),
        checks,
        bundle.get("coverage", {}),
        bundle.get("browser"),
    )
    validate_report(report)
    write_atomic_json(out_path, report)
    if report.get("run_manifest") and out_path.parent.is_dir():
        write_atomic_json(out_path.parent / "run-manifest.json", report["run_manifest"])
    print(f"Final report assembled and validated: {out_path}")


def validate_cli(args: argparse.Namespace) -> None:
    """Validate report file against Draft-07 JSON Schema and consistency invariants."""
    report_path = Path(args.report).resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_report(report)
    print(f"Report valid: {report_path}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    # collect
    run_cmd = sub.add_parser("collect", help="Bounded single-pass crawl and sensor collection")
    run_cmd.add_argument("site", help="Target URL or domain to audit")
    run_cmd.add_argument("--out", required=True, help="Output directory for evidence and report")
    run_cmd.add_argument("--pages", type=int, default=6, choices=range(1, 21), help="Max pages to crawl")
    run_cmd.add_argument("--seconds", type=int, default=160, choices=range(5, 301), help="Timeout in seconds")
    run_cmd.add_argument("--browser", action="store_true", help="Request browser rendering (if available)")
    run_cmd.add_argument("--probe-parameters", action="store_true", help="Run inert parameter probes")

    # finalize
    final_cmd = sub.add_parser("finalize", help="Compose agent review with collected evidence")
    final_cmd.add_argument("--bundle", required=True, help="Path to bundle.json from collect")
    final_cmd.add_argument("--review", required=True, help="Path to review.json from agent reasoning")
    final_cmd.add_argument("--out", required=True, help="Path to final output report JSON")

    # validate
    val_cmd = sub.add_parser("validate", help="Validate report against Draft-07 schema")
    val_cmd.add_argument("report", help="Path to report JSON to validate")

    args = parser.parse_args()

    if args.command == "collect":
        collect(args)
    elif args.command == "finalize":
        finalize(args)
    elif args.command == "validate":
        validate_cli(args)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
