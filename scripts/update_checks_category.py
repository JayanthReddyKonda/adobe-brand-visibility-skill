#!/usr/bin/env python3
"""Update checks.json to add category field alongside owner for all 134 checks."""
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKS_JSON = os.path.join(
    REPO_ROOT, "src", "skills", "audit-orchestrator", "references", "checks.json"
)


def get_category_for_check_id(check_id: str) -> str:
    if check_id.startswith(("A", "B", "C", "D", "E", "F", "G", "H")):
        return "technical"
    elif check_id.startswith("N"):
        return "content"
    elif check_id.startswith(("EC", "BC", "PP", "BN", "SA", "SC", "ED", "ME")):
        return "website-type"
    elif check_id.startswith("OS"):
        return "off-site"
    elif check_id.startswith("I"):
        return "bridge"
    elif check_id.startswith("J"):
        return "engagement"
    else:
        raise ValueError(f"Unknown check prefix: {check_id}")


def main():
    with open(CHECKS_JSON, "r", encoding="utf-8") as f:
        checks = json.load(f)

    for c in checks:
        c["category"] = get_category_for_check_id(c["check_id"])

    with open(CHECKS_JSON, "w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2)
    print(f"Updated {len(checks)} checks with category field.")


if __name__ == "__main__":
    main()
