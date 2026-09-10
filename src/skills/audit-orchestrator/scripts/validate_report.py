#!/usr/bin/env python3
import json
import os
import re
import sys


def validate_type(instance, schema, path="root"):
    expected_type = schema.get("type")
    if expected_type:
        type_list = expected_type if isinstance(expected_type, list) else [expected_type]
        type_map = {
            "object": dict,
            "array": list,
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "null": type(None),
        }
        valid = False
        for t in type_list:
            if t in type_map and isinstance(instance, type_map[t]):
                if t in ("integer", "number") and type(instance) is bool:
                    continue  # bool is a subclass of int, but we want strict checking
                valid = True
                break

        if not valid:
            return f"{path}: Expected {type_list}, got {type(instance).__name__}"

        if "string" in type_list and isinstance(instance, str) and schema.get("format") == "date-time":
            import datetime

            # P1-88: Strict timezone qualification requirement (e.g. 'Z' or '+00:00' / '-05:00')
            if not re.search(r"(Z|[+-]\d{2}:\d{2})$", instance):
                return f"{path}: '{instance}' is not a valid ISO 8601 date-time string (missing explicit timezone offset)"
            try:
                dt_str = instance.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(dt_str)
                if dt.tzinfo is None:
                    return f"{path}: '{instance}' is missing timezone offset"
            except ValueError:
                return f"{path}: '{instance}' is not a valid ISO 8601 date-time string"

        if "string" in type_list and isinstance(instance, str) and schema.get("format") == "uri":
            from urllib.parse import urlparse
            parsed = urlparse(instance)
            if not parsed.scheme or (parsed.scheme in ("http", "https") and not parsed.netloc):
                return f"{path}: '{instance}' is not a valid URI (missing scheme or host)"

    # Format checking when type is omitted but instance is string
    if not expected_type and isinstance(instance, str) and "format" in schema:
        fmt = schema["format"]
        if fmt == "date-time":
            import datetime
            if not re.search(r"(Z|[+-]\d{2}:\d{2})$", instance):
                return f"{path}: '{instance}' is not a valid ISO 8601 date-time string (missing explicit timezone offset)"
            try:
                dt_str = instance.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(dt_str)
                if dt.tzinfo is None:
                    return f"{path}: '{instance}' is missing timezone offset"
            except ValueError:
                return f"{path}: '{instance}' is not a valid ISO 8601 date-time string"
        elif fmt == "uri":
            from urllib.parse import urlparse
            parsed = urlparse(instance)
            if not parsed.scheme or (parsed.scheme in ("http", "https") and not parsed.netloc):
                return f"{path}: '{instance}' is not a valid URI (missing scheme or host)"

    # P1-89: Disallow NaN and Infinity numeric values
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        import math
        if math.isnan(instance) or math.isinf(instance):
            return f"{path}: Disallowed NaN or Infinity numeric value"

    if "minimum" in schema and isinstance(instance, (int, float)) and instance < schema["minimum"]:
        return f"{path}: Value {instance} is less than minimum {schema['minimum']}"

    if "maximum" in schema and isinstance(instance, (int, float)) and instance > schema["maximum"]:
        return f"{path}: Value {instance} is greater than maximum {schema['maximum']}"

    if "enum" in schema:
        matched = False
        for item in schema["enum"]:
            if instance == item and (type(instance) is bool) == (type(item) is bool):
                matched = True
                break
        if not matched:
            return f"{path}: Value {instance!r} not in allowed enum {schema['enum']}"

    if "const" in schema:
        c = schema["const"]
        if instance != c or (type(instance) is bool) != (type(c) is bool):
            return f"{path}: Value {instance!r} does not match const {c!r}"

    if "allOf" in schema and isinstance(schema["allOf"], list):
        for subschema in schema["allOf"]:
            err = validate_type(instance, subschema, path=path)
            if err:
                return err

    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        passed = False
        any_errs = []
        for subschema in schema["anyOf"]:
            err = validate_type(instance, subschema, path=path)
            if not err:
                passed = True
                break
            any_errs.append(err)
        if not passed:
            return f"{path}: Value does not match any allowed schema in anyOf ({'; '.join(any_errs[:2])})"

    if "oneOf" in schema and isinstance(schema["oneOf"], list):
        matches = 0
        one_errs = []
        for subschema in schema["oneOf"]:
            err = validate_type(instance, subschema, path=path)
            if not err:
                matches += 1
            else:
                one_errs.append(err)
        if matches != 1:
            return f"{path}: Value matched {matches} schemas in oneOf, expected exactly 1 ({'; '.join(one_errs[:2])})"

    if "minLength" in schema and isinstance(instance, str) and len(instance) < schema["minLength"]:
        return f"{path}: String too short, expected at least {schema['minLength']} chars"

    if "pattern" in schema and isinstance(instance, str) and not re.search(schema["pattern"], instance):
        return f"{path}: String does not match required pattern"

    if isinstance(instance, dict):
        if "required" in schema:
            for req in schema["required"]:
                if req not in instance:
                    return f"{path}: Missing required property '{req}'"

        for k, v in instance.items():
            if "properties" in schema and k in schema["properties"]:
                err = validate_type(v, schema["properties"][k], path=f"{path}.{k}")
                if err:
                    return err
            elif schema.get("additionalProperties") is False:
                return f"{path}: Additional property '{k}' not allowed"

    elif isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            return f"{path}: Too few items, expected at least {schema['minItems']}"
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            return f"{path}: Too many items, expected at most {schema['maxItems']}"
        if schema.get("uniqueItems"):
            try:
                if len({json.dumps(item, sort_keys=True) for item in instance}) != len(instance):
                    return f"{path}: Items must be unique"
            except (TypeError, ValueError):
                return f"{path}: Items cannot be checked for uniqueness"
        if "items" in schema:
            for i, item in enumerate(instance):
                err = validate_type(item, schema["items"], path=f"{path}[{i}]")
                if err:
                    return err

    return None


def verify_summary_counts(report):
    """Verify summary total_findings, categorical counts, and finding invariants."""
    errors = []
    findings = report.get("findings", [])
    summary = report.get("summary", {})

    if not isinstance(findings, list) or not isinstance(summary, dict):
        return errors

    status = report.get("audit_status")
    if status not in ("complete", "partial", "failed"):
        errors.append(f"Invalid or missing audit_status '{status}'. Must be 'complete', 'partial', or 'failed'")

    if "total_findings" not in summary:
        errors.append("summary is missing required property 'total_findings'")
    elif summary["total_findings"] != len(findings):
        errors.append(f"total_findings ({summary['total_findings']}) does not match findings count ({len(findings)})")

    expected = {
        sev: sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == sev)
        for sev in ("critical", "high", "medium", "low")
    }
    for sev, count in expected.items():
        if sev not in summary:
            errors.append(f"summary is missing required severity count '{sev}'")
        elif summary[sev] != count:
            errors.append(f"summary.{sev} ({summary[sev]}) does not match actual {sev} findings count ({count})")

    # Invariant: Duplicate finding IDs across standardized findings
    finding_ids = [
        f.get("id")
        for f in findings
        if isinstance(f, dict) and isinstance(f.get("id"), str) and re.match(r"^F-\d+$", f.get("id", ""))
    ]
    if len(set(finding_ids)) != len(finding_ids):
        errors.append("Duplicate finding ID detected in findings array")

    # Invariant: Duplicate proactive action IDs
    actions = report.get("proactive_actions", [])
    if isinstance(actions, list):
        action_ids = [a.get("id") for a in actions if isinstance(a, dict) and isinstance(a.get("id"), str)]
        if len(set(action_ids)) != len(action_ids):
            errors.append("Duplicate proactive action ID detected in proactive_actions array")

    # Invariant: actual_band to severity mapping and priority_index formula
    band_to_sev = {"S4": "critical", "S3": "high", "S2": "medium", "S1": "low", "S0": "info", "U": "unassessable"}
    for f in findings:
        if not isinstance(f, dict):
            continue
        band = f.get("actual_band")
        if band in band_to_sev and f.get("severity") and f["severity"] != band_to_sev[band]:
            errors.append(f"Finding {f.get('id')}: severity '{f.get('severity')}' does not match actual_band '{band}'")
        score = f.get("priority_index")
        d = f.get("difficulty")
        if score is not None and (
            band not in ("S1", "S2", "S3", "S4")
            or not isinstance(d, int)
            or not (1 <= d <= 5)
            or score != 5 * int(band[1]) + 6 - d
        ):
            errors.append(f"Finding {f.get('id')}: invalid or unsupported priority_index '{score}'")
    return errors


def validate_report_dict(report, schema_path=None):
    """Validate a Python dict report against schema and summary invariants.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    if not isinstance(report, dict):
        return False, ["Report must be a JSON object (dict)"]

    if schema_path is None:
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "report-schema.json"
        )
    if not os.path.exists(schema_path):
        return False, [f"Schema not found at {schema_path}"]

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    err = validate_type(report, schema)
    if err:
        errors.append(f"Schema validation failed: {err}")

    summary_errs = verify_summary_counts(report)
    if summary_errs:
        errors.extend(summary_errs)

    return (len(errors) == 0, errors)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Draft-07 JSON Schema validator for brand AI audit reports and telemetry."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="-",
        help="Path to report/payload JSON file or '-' for stdin (default: '-')",
    )
    parser.add_argument(
        "--schema",
        help="Path to Draft-07 schema JSON file (defaults to references/report-schema.json)",
    )
    args = parser.parse_args()

    if args.input_file != "-":
        if not os.path.exists(args.input_file):
            print(f"File not found: {args.input_file}", file=sys.stderr)
            sys.exit(2)
        with open(args.input_file, "r", encoding="utf-8") as f:
            data = f.read()
    else:
        if sys.stdin.isatty():
            parser.print_help(sys.stderr)
            sys.exit(2)
        data = sys.stdin.read()

    if not data.strip():
        print("Error: Empty JSON input received.", file=sys.stderr)
        sys.exit(2)

    def _reject_constant(c):
        raise ValueError(f"Disallowed JSON constant '{c}' (NaN and Infinity are not valid JSON)")

    try:
        instance = json.loads(data, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    if args.schema:
        schema_path = os.path.abspath(args.schema)
    else:
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "report-schema.json"
        )

    if not os.path.exists(schema_path):
        print(f"Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(2)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    err = validate_type(instance, schema)
    if err:
        print(f"Schema validation failed: {err}", file=sys.stderr)
        sys.exit(2)

    if schema_path.endswith("report-schema.json") and isinstance(instance, dict) and "summary" in instance:
        summary_errs = verify_summary_counts(instance)
        if summary_errs:
            print(f"Summary validation failed: {'; '.join(summary_errs)}", file=sys.stderr)
            sys.exit(2)

    schema_name = os.path.basename(schema_path)
    target_name = os.path.basename(args.input_file) if args.input_file != "-" else "stdin"
    print(f"Valid: {target_name} conforms to {schema_name}")
    sys.exit(0)


if __name__ == "__main__":
    main()
