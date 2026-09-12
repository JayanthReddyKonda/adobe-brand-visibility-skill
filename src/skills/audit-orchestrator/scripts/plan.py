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


def calculate_priority_index(severity: int, difficulty: int) -> int:
    """Calculate task ranking index: priority_index = 5 * severity + (6 - difficulty)."""
    if not (1 <= severity <= 4):
        raise ValueError(f"severity must be in 1..4, got {severity}")
    if not (1 <= difficulty <= 5):
        raise ValueError(f"difficulty must be in 1..5, got {difficulty}")
    return 5 * severity + (6 - difficulty)


def infer_finding_difficulty(f: Dict[str, Any]) -> int:
    """Infer remediation difficulty (1=easiest, 5=hardest) from solution level or category."""
    d = f.get("difficulty")
    if isinstance(d, int) and 1 <= d <= 5:
        return d
    sol_level = str(f.get("solution_level", "")).upper()
    if sol_level == "E":  # Editorial copy update
        return 2
    if sol_level == "V":  # Mechanical validation / config / robots.txt
        return 2
    if sol_level == "C":  # Code / structured data / server template
        return 3
    if sol_level == "X":  # External platform claim / third-party profile
        return 4

    cat = str(f.get("category", "")).lower()
    cid = str(f.get("cause_id") or f.get("id") or "").lower()
    if "robots" in cat or "robots" in cid or "sitemap" in cid:
        return 2
    if "entity" in cat or "schema" in cat:
        return 2
    if "geo" in cat or "citability" in cat:
        return 2
    if "engagement" in cat:
        return 2
    if "fact" in cat or "drift" in cid:
        return 3
    if "corroboration" in cat or "authority" in cat or "backlink" in cid:
        return 4
    return 3


def main():
    import argparse
    import json
    import os
    import sys

    parser = argparse.ArgumentParser(description="Remediation planning and priority index calculator.")
    parser.add_argument("--finding", help="Path to finding JSON file or inline JSON string")
    parser.add_argument("--rule", help="Path to rule/check JSON file or inline JSON string (optional)")
    parser.add_argument("--report", help="Path to report JSON file to rank all findings")
    parser.add_argument("--severity", type=int, choices=[1, 2, 3, 4], help="Severity level (1=low, 2=medium, 3=high, 4=critical)")
    parser.add_argument("--difficulty", type=int, choices=[1, 2, 3, 4, 5], help="Difficulty level (1=easiest, 5=hardest)")
    parser.add_argument("--output", help="Path to write output JSON (optional, defaults to stdout)")
    args = parser.parse_args()

    formatted_output = ""

    if args.severity is not None and args.difficulty is not None:
        idx = calculate_priority_index(args.severity, args.difficulty)
        formatted_output = json.dumps({
            "severity": args.severity,
            "difficulty": args.difficulty,
            "priority_index": idx,
            "formula": "5 * severity + (6 - difficulty)",
        }, indent=2)

    elif args.report:
        if not os.path.exists(args.report):
            sys.stderr.write(f"Error: Report file {args.report} not found\n")
            sys.exit(1)
        with open(args.report, "r", encoding="utf-8") as f:
            data = json.load(f)
        findings = data.get("findings", [])
        sev_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        ranked = []
        for f in findings:
            sev_num = sev_map.get(str(f.get("severity", "medium")).lower(), 2)
            diff_num = infer_finding_difficulty(f)
            p_idx = calculate_priority_index(sev_num, diff_num)
            ranked.append({
                "id": f.get("id"),
                "title": f.get("title"),
                "severity": f.get("severity"),
                "difficulty": diff_num,
                "priority_index": p_idx,
                "queue": f.get("queue", "confirmed"),
            })
        ranked.sort(key=lambda x: x["priority_index"], reverse=True)
        formatted_output = json.dumps({"total_ranked": len(ranked), "roadmap": ranked}, indent=2)

    elif args.finding:
        try:
            if os.path.exists(args.finding):
                with open(args.finding, "r", encoding="utf-8") as f:
                    finding_data = json.load(f)
            else:
                finding_data = json.loads(args.finding)
        except Exception as e:
            sys.stderr.write(f"Error: Failed to parse finding: {e}\n")
            sys.exit(1)

        rule = {}
        if args.rule:
            try:
                if os.path.exists(args.rule):
                    with open(args.rule, "r", encoding="utf-8") as f:
                        rule = json.load(f)
                else:
                    rule = json.loads(args.rule)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to parse rule: {e}\n")

        planned = plan(finding_data, rule)
        formatted_output = json.dumps(planned, indent=2)

    else:
        parser.print_help()
        return

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_output)
            f.write("\n")
        print(f"Plan written to {args.output}")
    else:
        print(formatted_output)


if __name__ == "__main__":
    main()

