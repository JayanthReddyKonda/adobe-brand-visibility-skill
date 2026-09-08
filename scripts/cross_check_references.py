#!/usr/bin/env python3
"""Cross-check checks.json against all checks.md reference files in skills."""
import glob
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKS_JSON = os.path.join(
    REPO_ROOT, "src", "skills", "audit-orchestrator", "references", "checks.json"
)


def cross_check():
    with open(CHECKS_JSON, "r", encoding="utf-8") as f:
        json_checks = json.load(f)
    json_ids = {c["check_id"]: c for c in json_checks}

    md_files = glob.glob(
        os.path.join(REPO_ROOT, "src", "skills", "**", "references", "checks.md"),
        recursive=True,
    )

    md_check_ids = {}
    for m in md_files:
        rel_path = os.path.relpath(m, REPO_ROOT)
        with open(m, "r", encoding="utf-8") as f:
            content = f.read()
        found = re.findall(r"^##\s+([A-Za-z0-9_]+)", content, re.MULTILINE)
        for fid in found:
            md_check_ids.setdefault(fid, []).append(rel_path)

    in_json_not_md = set(json_ids.keys()) - set(md_check_ids.keys())
    in_md_not_json = set(md_check_ids.keys()) - set(json_ids.keys())

    print(f"Total checks in checks.json: {len(json_ids)}")
    print(f"Total unique IDs across checks.md: {len(md_check_ids)}")
    print(f"Found {len(md_files)} checks.md files:")
    for m in sorted(md_files):
        print(f"  - {os.path.relpath(m, REPO_ROOT)}")

    if in_json_not_md:
        print(f"\n[ORPHANS] In checks.json but missing in checks.md ({len(in_json_not_md)}):")
        for cid in sorted(in_json_not_md):
            print(f"  {cid}: {json_ids[cid].get('title', '')}")

    if in_md_not_json:
        print(f"\n[ORPHANS] In checks.md but missing in checks.json ({len(in_md_not_json)}):")
        for cid in sorted(in_md_not_json):
            print(f"  {cid}: found in {md_check_ids[cid]}")

    if not in_json_not_md and not in_md_not_json:
        print("\n[PERFECT JOIN] Zero orphans detected between checks.json and all checks.md files.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(cross_check())
