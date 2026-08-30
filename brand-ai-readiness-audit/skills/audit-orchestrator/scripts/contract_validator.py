#!/usr/bin/env python3
"""
validate_report.py - Validates an audit report against the Brand AI-Readiness Audit JSON Schema.
Zero external dependencies (uses Python standard library).
"""

import sys
import os
import json
import re
import argparse
from datetime import datetime

def validate_iso8601(timestamp_str):
    """Validate ISO 8601 UTC timestamp format."""
    if not isinstance(timestamp_str, str):
        return False
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$'
    return bool(re.match(iso_pattern, timestamp_str))

def validate_report_dict(data):
    """Validate report dictionary against the required schema."""
    errors = []
    
    # 1. Top-level required fields
    for field in ["site", "audited_at", "summary", "findings"]:
        if field not in data:
            errors.append(f"Missing top-level required field: '{field}'")

    if errors:
        return False, errors

    # Check site
    if not isinstance(data["site"], str) or not data["site"].strip():
        errors.append("'site' must be a non-empty string")

    # Check audited_at
    if not validate_iso8601(data["audited_at"]):
        errors.append(f"'audited_at' must be a valid ISO 8601 timestamp (e.g., '2026-09-20T14:32:00Z'), got '{data.get('audited_at')}'")

    # Check optional/recommended audit_status
    if "audit_status" in data:
        if data["audit_status"] not in ("ok", "partial", "inconclusive"):
            errors.append(f"'audit_status' must be one of ['ok', 'partial', 'inconclusive'], got '{data.get('audit_status')}'")


    # Check summary
    summary = data.get("summary")
    if not isinstance(summary, dict):
        errors.append("'summary' must be an object")
    else:
        for sum_field in ["total_findings", "critical", "high", "medium"]:
            if sum_field not in summary:
                errors.append(f"Summary missing required field: '{sum_field}'")
            elif not isinstance(summary[sum_field], int) or summary[sum_field] < 0:
                errors.append(f"Summary field '{sum_field}' must be a non-negative integer")

    # Check findings
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("'findings' must be an array")
    else:
        severities_found = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        valid_severities = {"critical", "high", "medium", "low", "info"}
        valid_priorities = {"critical", "high", "medium", "low"}

        for idx, finding in enumerate(findings):
            prefix = f"findings[{idx}]"
            if not isinstance(finding, dict):
                errors.append(f"{prefix} must be an object")
                continue

            for req in ["id", "title", "severity", "evidence", "suggested_action"]:
                if req not in finding:
                    errors.append(f"{prefix} missing required field: '{req}'")

            # Check severity
            sev = finding.get("severity")
            if sev not in valid_severities:
                errors.append(f"{prefix}.severity must be one of {list(valid_severities)}, got '{sev}'")
            else:
                severities_found[sev] = severities_found.get(sev, 0) + 1

            # Check evidence
            ev = finding.get("evidence")
            if not isinstance(ev, str) or len(ev.strip()) < 5:
                errors.append(f"{prefix}.evidence must be a descriptive string with at least 5 characters")

            # Check suggested_action
            action = finding.get("suggested_action")
            if not isinstance(action, dict):
                errors.append(f"{prefix}.suggested_action must be an object")
            else:
                if "summary" not in action or not isinstance(action["summary"], str) or len(action["summary"].strip()) < 5:
                    errors.append(f"{prefix}.suggested_action.summary must be a non-empty string (min length 5)")
                
                pri = action.get("priority")
                if pri not in valid_priorities:
                    errors.append(f"{prefix}.suggested_action.priority must be one of {list(valid_priorities)}, got '{pri}'")

        # Cross-verify summary counts with findings
        if isinstance(summary, dict) and "total_findings" in summary:
            if summary["total_findings"] != len(findings):
                errors.append(f"Summary total_findings ({summary['total_findings']}) does not match findings count ({len(findings)})")
            for level in ["critical", "high", "medium"]:
                if level in summary and summary[level] != severities_found.get(level, 0):
                    errors.append(f"Summary {level} count ({summary[level]}) does not match actual findings with severity '{level}' ({severities_found.get(level, 0)})")

    return len(errors) == 0, errors

def main():
    parser = argparse.ArgumentParser(
        description="Validate a Brand AI-Readiness Audit report against the official schema."
    )
    parser.add_argument("report_file", help="Path to JSON report file (or '-' to read from stdin)")
    parser.add_argument("--quiet", action="store_true", help="Only output exit code, suppress messages")
    
    args = parser.parse_args()

    try:
        if args.report_file == "-":
            content = sys.stdin.read()
        else:
            with open(args.report_file, "r", encoding="utf-8") as f:
                content = f.read()

        data = json.loads(content)
    except Exception as e:
        if not args.quiet:
            sys.stderr.write(f"Error reading/parsing JSON: {e}\n")
        sys.exit(1)

    is_valid, errors = validate_report_dict(data)

    if is_valid:
        if not args.quiet:
            print("Validation successful: Report conforms 100% to Brand AI-Readiness Audit schema.")
        sys.exit(0)
    else:
        if not args.quiet:
            sys.stderr.write("Validation failed with the following errors:\n")
            for err in errors:
                sys.stderr.write(f"  - {err}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

