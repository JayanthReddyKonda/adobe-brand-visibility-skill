#!/usr/bin/env python3
import sys
import json
import os

try:
    import jsonschema
except ImportError:
    print("Warning: jsonschema library is required for validation. Skipping.", file=sys.stderr)
    sys.exit(0)

def main():
    if "-" in sys.argv:
        data = sys.stdin.read()
    else:
        print("Usage: python3 validate_report.py - < report.json", file=sys.stderr)
        sys.exit(1)

    try:
        report = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "report-schema.json")
    if not os.path.exists(schema_path):
        print(f"Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(1)

    with open(schema_path, "r") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=report, schema=schema)
        # Echo valid JSON back out
        print(json.dumps(report))
        sys.exit(0)
    except jsonschema.exceptions.ValidationError as e:
        print(f"Schema validation failed: {e.message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
