#!/usr/bin/env python3
import sys
import json
import os
import re

def validate_type(instance, schema, path="root"):
    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "object" and not isinstance(instance, dict):
            return f"{path}: Expected object, got {type(instance).__name__}"
        elif expected_type == "array" and not isinstance(instance, list):
            return f"{path}: Expected array, got {type(instance).__name__}"
        elif expected_type == "string":
            if not isinstance(instance, str):
                return f"{path}: Expected string, got {type(instance).__name__}"
            # P0-50: Strictly enforce date-time format
            if schema.get("format") == "date-time":
                import datetime
                try:
                    dt_str = instance.replace('Z', '+00:00')
                    datetime.datetime.fromisoformat(dt_str)
                except ValueError:
                    return f"{path}: '{instance}' is not a valid ISO 8601 date-time string"
        elif expected_type == "integer" and not isinstance(instance, int):
            return f"{path}: Expected integer, got {type(instance).__name__}"
        elif expected_type == "number" and not isinstance(instance, (int, float)):
            return f"{path}: Expected number, got {type(instance).__name__}"
            
    if "enum" in schema:
        if instance not in schema["enum"]:
            return f"{path}: Value {repr(instance)} not in allowed enum {schema['enum']}"
            
    if "minLength" in schema and isinstance(instance, str):
        if len(instance) < schema["minLength"]:
            return f"{path}: String too short, expected at least {schema['minLength']} chars"

    if expected_type == "object":
        if "required" in schema:
            for req in schema["required"]:
                if req not in instance:
                    return f"{path}: Missing required property '{req}'"
        
        for k, v in instance.items():
            if "properties" in schema and k in schema["properties"]:
                err = validate_type(v, schema["properties"][k], path=f"{path}.{k}")
                if err: return err
            elif schema.get("additionalProperties") is False:
                return f"{path}: Additional property '{k}' not allowed"

    elif expected_type == "array":
        if "items" in schema:
            for i, item in enumerate(instance):
                err = validate_type(item, schema["items"], path=f"{path}[{i}]")
                if err: return err

    return None

def main():
    if "-" in sys.argv:
        data = sys.stdin.read()
    else:
        print("Usage: python3 validate_report.py - < report.json", file=sys.stderr)
        sys.exit(2)

    try:
        report = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(2)

    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "report-schema.json")
    if not os.path.exists(schema_path):
        print(f"Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(2)

    with open(schema_path, "r") as f:
        schema = json.load(f)

    err = validate_type(report, schema)
    if err:
        print(f"Schema validation failed: {err}", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(report, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
