"""Reconcile remedy readiness independently of observation severity.

Pure Python standard library.
Consolidated interface forwarding to canonical orchestrator planning algorithms.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from orchestrator import (
        LABELS,
        calculate_priority_index,
        generate_priority_justification,
        infer_finding_difficulty,
        plan,
        resolve_dag_node,
    )
except ImportError:
    LABELS: Dict[str, str] = {
        "S4": "critical",
        "S3": "high",
        "S2": "medium",
        "S1": "low",
        "S0": "info",
        "U": "unassessable",
    }

    def calculate_priority_index(severity: int, difficulty: int) -> int:
        if not (1 <= severity <= 4):
            raise ValueError(f"severity must be in 1..4, got {severity}")
        if not (1 <= difficulty <= 5):
            raise ValueError(f"difficulty must be in 1..5, got {difficulty}")
        return 5 * severity + (6 - difficulty)

    def infer_finding_difficulty(f: Dict[str, Any]) -> int:
        return 2

    def plan(item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        return dict(item)

    def resolve_dag_node(cid: str, cat: str) -> str:
        return "RETRIEVAL"

    def generate_priority_justification(f: Dict[str, Any], idx: int) -> str:
        return f"Rank #{idx}: Prioritized based on severity and DAG hierarchy."


def main():
    import argparse
    import json
    import os
    import sys

    parser = argparse.ArgumentParser(description="Remediation planning and priority index calculator.")
    parser.add_argument("--finding", help="Path to finding JSON file or inline JSON string")
    parser.add_argument("--rule", help="Path to rule/check JSON file or inline JSON string (optional)")
    parser.add_argument("--report", "--input", "-i", dest="report", help="Path to report JSON file to rank all findings")
    parser.add_argument("--rank-findings", dest="rank_findings", help="Path to findings JSON file or inline JSON string to rank with causal DAG order and justifications")
    parser.add_argument("--severity", type=int, choices=[1, 2, 3, 4], help="Severity level (1=low, 2=medium, 3=high, 4=critical)")
    parser.add_argument("--difficulty", type=int, choices=[1, 2, 3, 4, 5], help="Difficulty level (1=easiest, 5=hardest)")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="Output format (default: auto-inferred from output or json)")
    parser.add_argument("--output", "-o", help="Path to write output JSON/Markdown (optional, defaults to stdout)")
    parser.add_argument("--top", "-n", type=int, default=None, help="Limit output to top N ranked findings (optional)")
    args = parser.parse_args()

    if args.format is None:
        if args.output and args.output.lower().endswith((".md", ".markdown")):
            args.format = "markdown"
        else:
            args.format = "json"

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
        if args.top is not None and args.top > 0:
            ranked = ranked[:args.top]
        if args.format == "markdown":
            lines = [f"# Priority Remediation Roadmap ({len(ranked)} items)\n"]
            for r_idx, r in enumerate(ranked, 1):
                lines.append(f"{r_idx}. **[{str(r.get('severity', 'medium')).upper()}] {r.get('id', 'F')}: {r.get('title', '')}** (Priority Index: {r.get('priority_index')}, Difficulty: {r.get('difficulty')}/5)")
            formatted_output = "\n".join(lines) + "\n"
        else:
            formatted_output = json.dumps({"total_ranked": len(ranked), "roadmap": ranked}, indent=2)

    elif args.rank_findings:
        try:
            if os.path.exists(args.rank_findings):
                with open(args.rank_findings, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(args.rank_findings)
        except Exception as e:
            sys.stderr.write(f"Error: Failed to parse findings: {e}\n")
            sys.exit(1)

        raw_list = data.get("findings", data) if isinstance(data, dict) else data
        if not isinstance(raw_list, list):
            raw_list = [raw_list]

        sev_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        dag_order = {
            "RETRIEVAL": 7,
            "RENDERING": 6,
            "ENTITY": 5,
            "CORROBORATION": 4,
            "FACTS": 3,
            "GEO_CITABILITY": 2,
            "ENGAGEMENT": 1,
        }

        enriched = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            item_copy = dict(item)
            cid = str(item_copy.get("cause_id") or item_copy.get("id") or "")
            cat = str(item_copy.get("category") or "")
            dag = item_copy.get("dag_node") or resolve_dag_node(cid, cat)
            item_copy["dag_node"] = dag
            if isinstance(item_copy.get("severity"), int):
                sev_num = item_copy["severity"]
            elif str(item_copy.get("severity", "")).isdigit():
                sev_num = int(item_copy["severity"])
            else:
                sev_num = sev_map.get(str(item_copy.get("severity", "medium")).lower(), 2)
            diff_num = infer_finding_difficulty(item_copy)
            p_idx = calculate_priority_index(sev_num, diff_num)
            item_copy["priority_index"] = p_idx
            enriched.append((sev_num, dag_order.get(dag, 0), p_idx, item_copy))

        # Sort by severity descending, DAG tier descending, priority_index descending
        enriched.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

        ranked = []
        for idx, (_, _, _, f) in enumerate(enriched, 1):
            f["priority_rank"] = idx
            f["priority_justification"] = generate_priority_justification(f, idx)
            ranked.append(f)
        if args.top is not None and args.top > 0:
            ranked = ranked[:args.top]

        formatted_output = json.dumps({"status": "ok", "total_ranked": len(ranked), "roadmap": ranked}, indent=2)

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
