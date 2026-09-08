"""Reconcile remedy readiness independently of observation severity.

Pure Python standard library.
"""
from typing import Any, Dict

LABELS: Dict[str, str] = {
    "S4": "critical",
    "S3": "high",
    "S2": "medium",
    "S1": "low",
    "S0": "info",
    "U": "unassessable",
}


def plan(item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate disposition, queue, remedy readiness, and priority index for an audit item."""
    item = dict(item)
    level = rule.get("solution_level", "C")
    item["solution_level"] = level
    item["reference_band"] = rule.get("reference_band", "S2")
    item["benefit_area"] = {"G": ["geo"], "E": ["engagement"], "B": ["geo", "engagement"]}.get(
        rule.get("benefit_area", "G"), ["geo"]
    )
    kind = item.get("finding_kind", "confirmed_problem")
    if kind == "informational_observation":
        return item
    ready = item.get("remedy_readiness") == "ready"
    if level == "X":
        item.update(disposition="insufficient_evidence", remedy_readiness="not_possible")
        ready = False
    elif level == "E":
        item.update(disposition="editorial_draft", finding_kind="advisory")
    elif ready and level == "V" and item.get("candidate") and item.get("validation_results"):
        item["disposition"] = "validated_candidate"
    else:
        item["disposition"] = "conditional_proposal"
        item["remedy_readiness"] = "needs_context"
        ready = False
    # A C remedy may be ready only after explicit missing-context resolution and tests
    if level == "C" and item.get("resolved_context") and item.get("validation_results") and item.get("suggested_action"):
        ready = True
        item["remedy_readiness"] = "ready"
    item["queue"] = "advisory" if item.get("finding_kind") == "advisory" else "confirmed" if ready else "investigation"
    item.setdefault("difficulty", None)
    item.setdefault("difficulty_range", None)
    item.setdefault("depends_on", [])
    if not ready:
        item["difficulty"] = None
    band = item.get("actual_band", "S2")
    d = item.get("difficulty")
    item["priority_index"] = (
        5 * int(band[1]) + (6 - d)
        if band in ("S1", "S2", "S3", "S4") and isinstance(d, int) and 1 <= d <= 5 and ready
        else None
    )
    if item.get("difficulty_range") and ready and band in ("S1", "S2", "S3", "S4"):
        lo, hi = item["difficulty_range"]
        item["priority_index_range"] = [5 * int(band[1]) + 6 - hi, 5 * int(band[1]) + 6 - lo]
    severity = LABELS.get(band, "medium")
    action = dict(item.get("suggested_action") or {})
    action.setdefault("summary", f"For {item.get('scope', '')}: {rule.get('solution', '')}")
    action.setdefault("technical_fix", f"Remediate {item.get('check_id', '')} according to technical specifications.")
    action.setdefault("creative_fix", None)
    action.setdefault("verification", "Inspect live response to confirm remediation.")
    action["priority"] = severity if severity in ("critical", "high", "medium", "low") else "medium"
    action.setdefault(
        "acceptance_tests",
        [
            "Recollect the exact cited scope after an owner-approved change.",
            "Verify the original predicate and unaffected contexts; no live change is applied by this audit.",
        ],
    )
    action.setdefault(
        "missing_context",
        []
        if ready
        else ["Owner intent, correct source values, implementation location and representative regression environment as specified in this check"],
    )
    item["suggested_action"] = action
    return item
