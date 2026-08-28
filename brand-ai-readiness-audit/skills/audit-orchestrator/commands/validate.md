---
description: Validate an existing audit report against the official Brand AI-Readiness Audit schema
argument-hint: <path-to-report.json>
---

Validate a previously generated audit report JSON file against the official schema and report compliance.

## Procedure

1. Locate the target report JSON file in the workspace.
2. Run the bundled validator:
   ```bash
   python3 skills/audit-orchestrator/scripts/validate_report.py <path-to-report.json>
   ```
   *(On Windows, use `python` or `py`.)*
3. Report the validation result: pass/fail and any missing or malformed fields.

## Notes

- If no report file is given, instruct the user to run `/audit` first, or point to an existing `report.json`.