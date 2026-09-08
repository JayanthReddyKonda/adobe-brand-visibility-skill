"""Evidence gate, cause-scoped deduplication, queue ordering and schema validation.

Pure Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from plan import LABELS, plan
from validate_report import validate_report_dict


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_evidence(item: Dict[str, Any], artifacts: Dict[str, Any]) -> None:
    """Gate every candidate finding through strict immutable evidence verification."""
    refs = item.get("evidence_refs", [])
    if not refs:
        raise ValueError("Missing evidence references")
    for ref in refs:
        artifact = artifacts.get(ref.get("artifact"))
        if artifact is None:
            raise ValueError("Evidence artifact not found")
        quote = ref.get("quote")
        if not isinstance(quote, str) or not quote or not ref.get("locator"):
            raise ValueError("Exact quote and locator required")
        locator = ref["locator"]
        if locator in ("response body", "response"):
            locator = "text"
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*(?:\[\d+\])?(?:\.[A-Za-z_][A-Za-z_0-9]*(?:\[\d+\])?)*", locator):
            raise ValueError("Unsupported evidence locator grammar")
        selected: Any = artifact
        try:
            for part in locator.split("."):
                m = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9]*)(?:\[(\d+)\])?", part)
                if not m:
                    raise ValueError("Malformed locator")
                selected = selected[m.group(1)]
                if m.group(2) is not None:
                    selected = selected[int(m.group(2))]
        except (KeyError, TypeError, IndexError):
            raise ValueError("Evidence locator does not resolve")
        haystack = selected if isinstance(selected, str) else json.dumps(selected, ensure_ascii=False)
        if (
            quote not in haystack
            and json.dumps(quote, ensure_ascii=False)[1:-1] not in haystack
            and not (locator == "source.canonicals" and all(q in haystack for q in quote.split(" | ")))
        ):
            raise ValueError("Quote not found at cited locator")
    if item.get("finding_kind") == "confirmed_problem" and not item.get("collection_complete_for_scope"):
        raise ValueError("Confirmed problem lacks complete evidence for its narrow scope")
    if not item.get("severity_reason") or not item.get("scope"):
        raise ValueError("Scope and activated severity reason required")


def sort_tasks(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort audit tasks topologically by dependency DAG, lane queues, severity, and difficulty."""
    queues = {"confirmed": 0, "advisory": 1, "investigation": 2}

    def key(item: Dict[str, Any]) -> tuple:
        band = item.get("actual_band", "S2")
        severity = int(band[1]) if band.startswith("S") and len(band) > 1 else -1
        d = item.get("difficulty")
        return (
            queues.get(item.get("queue", "confirmed"), 0),
            -severity,
            d if d is not None else 0,
            -len(set(item.get("affected_urls", [item.get("scope", "")]))),
            -int(item.get("established_importance", 0)),
            item.get("id", ""),
        )

    pending = {i["id"]: i for i in items}
    done: set[str] = set()
    output: List[Dict[str, Any]] = []
    for item in items:
        for dep in item.get("depends_on", []):
            if dep not in pending:
                raise ValueError("Unknown prerequisite: " + dep)
            if queues.get(pending[dep].get("queue", "confirmed"), 0) > queues.get(item.get("queue", "confirmed"), 0):
                raise ValueError("Unresolved cross-queue prerequisite; move dependent to investigation")

    while pending:
        available = [i for i in pending.values() if set(i.get("depends_on", [])) <= done]
        if not available:
            raise ValueError("Dependency cycle")
        first = min(available, key=key)
        output.append(first)
        done.add(first["id"])
        del pending[first["id"]]
    return output


def validate_report(report: Dict[str, Any]) -> bool:
    """Validate report dictionary against schema and count invariants."""
    schema_path = Path(__file__).resolve().parents[1] / "references/report-schema.json"
    valid, errors = validate_report_dict(report, str(schema_path))
    if not valid:
        raise ValueError("; ".join(errors))
    return True


def assemble(
    site: str,
    candidates: List[Dict[str, Any]],
    records: List[Dict[str, Any]],
    checks: List[Dict[str, Any]],
    coverage: Dict[str, Any],
    browser: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble final synthesized report from candidate findings and collected inventory."""
    artifacts = {a["artifact"]: a for a in records if isinstance(a, dict) and a.get("artifact")}
    artifacts.update({a["artifact"]: a for a in (browser or {}).get("captures", []) if isinstance(a, dict) and a.get("artifact")})
    catalogue = {c["check_id"]: c for c in checks}
    observations: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    merged: Dict[Any, Dict[str, Any]] = {}

    for index, item in enumerate(candidates):
        try:
            item = dict(item)
            check = catalogue.get(item["check_id"])
            if not check:
                raise ValueError(f"Unknown check_id: {item.get('check_id')}")
            if item["actual_band"] not in LABELS:
                raise ValueError("Invalid actual band")
            if item["finding_kind"] not in ("confirmed_problem", "advisory", "investigation", "informational_observation"):
                raise ValueError("Unknown finding kind")
            if item["finding_kind"] == "confirmed_problem" and item["actual_band"] in ("S0", "U"):
                raise ValueError("Unassessable/no-change item cannot be a confirmed problem")
            if item["finding_kind"] == "confirmed_problem" and check.get("feasibility", "").startswith(("Not possible", "Exclude")):
                raise ValueError("Check cannot support automated confirmed failure")
            if item.get("difficulty") is not None and (
                not isinstance(item["difficulty"], int) or not 1 <= item["difficulty"] <= 5 or not item.get("difficulty_reason")
            ):
                raise ValueError("Difficulty requires D1-D5 and a justification")
            if item.get("difficulty_range") is not None:
                rg = item["difficulty_range"]
                if len(rg) != 2 or any(not isinstance(x, int) for x in rg) or not 1 <= rg[0] <= rg[1] <= 5:
                    raise ValueError("Invalid difficulty interval")
            verify_evidence(item, artifacts)
            item = plan(item, check)
            if item["finding_kind"] == "informational_observation" or item["actual_band"] == "S0":
                observations.append(item)
                continue
            ids = sorted(set(item.get("related_check_ids", []) + [item["check_id"]]))
            if any(i not in catalogue for i in ids):
                raise ValueError("Unknown related check ID")
            evidence_key = tuple(sorted((e["artifact"], e["locator"]) for e in item["evidence_refs"]))
            cause = item.get("root_cause_key")
            if cause and not item.get("root_cause_reason"):
                raise ValueError("Explicit root cause requires reasoning")
            dedup = (item["scope"], item["finding_kind"], cause or evidence_key)
            item["related_check_ids"] = ids
            item["id"] = item.get("id") or "F-" + hashlib.sha256(repr(dedup).encode()).hexdigest()[:12]
            if dedup in merged:
                prev = merged[dedup]
                prev["related_check_ids"] = sorted(set(prev["related_check_ids"] + ids))
                prev["evidence_refs"] += [e for e in item["evidence_refs"] if e not in prev["evidence_refs"]]
                curr_band_num = int(item["actual_band"][1]) if item["actual_band"].startswith("S") else -1
                prev_band_num = int(prev["actual_band"][1]) if prev["actual_band"].startswith("S") else -1
                if curr_band_num > prev_band_num:
                    prev["actual_band"] = item["actual_band"]
                prev["depends_on"] = sorted(set(prev["depends_on"] + item["depends_on"]))
                prev["priority_index"] = None
                prev["difficulty"] = None
            else:
                merged[dedup] = item
        except (ValueError, KeyError, TypeError) as exc:
            dropped.append(dict(candidate_index=index, check_id=item.get("check_id"), reason=str(exc)))

    findings = sort_tasks(list(merged.values()))
    for item in findings:
        item["severity"] = LABELS[item["actual_band"]]
        item["evidence"] = "; ".join(f"{e['artifact']} at {e['locator']}: {e['quote'][:500]}" for e in item["evidence_refs"])
        item.setdefault("category", "crawlability" if item.get("check_id", "").startswith(("B", "D")) else "structured_data" if item.get("check_id", "").startswith("E") else "content_quality")
        item.setdefault("root_cause", item.get("severity_reason") or item.get("observation", "Defect identified"))
        item.setdefault("confidence", "high")
        action = dict(item.get("suggested_action") or {})
        action.setdefault("technical_fix", f"Technical remediation for {item.get('check_id', '')}.")
        action.setdefault("creative_fix", None)
        action.setdefault("verification", "Verify remediation in production.")
        item["suggested_action"] = action
    summary = dict(
        total_findings=len(findings),
        **{v: sum(i["severity"] == v for i in findings) for v in ("critical", "high", "medium", "low")}
    )
    summary["confirmed_problems"] = sum(i["finding_kind"] == "confirmed_problem" for i in findings)
    report = dict(
        site=site,
        audited_at=now(),
        audit_status="complete",
        summary=summary,
        findings=findings,
        observations=observations,
        dropped_findings=dropped,
        coverage=coverage,
        limitations=[
            "An empty findings array is not a pass.",
            "No citation, traffic or conversion uplift is measured.",
            "Recommendations only; no changes were applied to the website.",
        ],
        proactive_actions=[],
    )
    validate_report(report)
    return report
