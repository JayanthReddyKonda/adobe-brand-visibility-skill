#!/usr/bin/env python3
"""
sync.py - Cross-platform runtime mirror synchronization script.
Mirrors src/skills/ to .agents/skills/ and build/brand-ai-readiness-audit/skills/.
"""

import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SRC_SKILLS = os.path.join(PROJECT_ROOT, "src", "skills")
AGENTS_SKILLS = os.path.join(PROJECT_ROOT, ".agents", "skills")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
AGENTS_DIR = os.path.join(PROJECT_ROOT, ".agents")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", "brand-ai-readiness-audit")
BRAND_AUDIT_AGENTS = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "brand_audit", ".agents"))


def sync_tree(src: str, dst: str):
    """Recursively synchronize src to dst, deleting extraneous files and ignoring cache."""
    os.makedirs(dst, exist_ok=True)
    src_entries = set(os.listdir(src))
    dst_entries = set(os.listdir(dst))

    # Remove extra in dst
    for item in dst_entries - src_entries:
        target = os.path.join(dst, item)
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            try:
                os.remove(target)
            except OSError:
                pass

    # Copy / update from src to dst
    for item in src_entries:
        if item in ("__pycache__", ".DS_Store") or item.endswith(".pyc"):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            sync_tree(s, d)
        else:
            if not os.path.exists(d) or os.path.getmtime(s) > os.path.getmtime(d):
                shutil.copy2(s, d)


def main():
    print("=== Synchronizing Skills and Marketplace Manifests ===")

    # 1. Sync src/skills/ -> .agents/skills/
    print("Syncing src/skills/ to .agents/skills/...")
    sync_tree(SRC_SKILLS, AGENTS_SKILLS)

    # 2. Sync root manifests
    for manifest in ("marketplace.json", "README.md", "LICENSE"):
        src_m = os.path.join(SRC_DIR, manifest)
        dst_m = os.path.join(AGENTS_DIR, manifest)
        if os.path.exists(src_m):
            shutil.copy2(src_m, dst_m)

    # 3. If build directory exists, sync to build/brand-ai-readiness-audit
    if os.path.isdir(BUILD_DIR):
        print("Syncing to build/brand-ai-readiness-audit...")
        build_skills = os.path.join(BUILD_DIR, "skills")
        sync_tree(SRC_SKILLS, build_skills)
        for manifest in ("marketplace.json", "README.md", "LICENSE"):
            src_m = os.path.join(SRC_DIR, manifest)
            dst_m = os.path.join(BUILD_DIR, manifest)
            if os.path.exists(src_m):
                shutil.copy2(src_m, dst_m)

    # 4. If ../brand_audit/.agents exists, sync to brand_audit/.agents
    if os.path.isdir(BRAND_AUDIT_AGENTS) or os.path.isdir(os.path.dirname(BRAND_AUDIT_AGENTS)):
        print(f"Syncing to {BRAND_AUDIT_AGENTS}...")
        brand_audit_skills = os.path.join(BRAND_AUDIT_AGENTS, "skills")
        sync_tree(SRC_SKILLS, brand_audit_skills)
        for manifest in ("marketplace.json", "README.md", "LICENSE"):
            src_m = os.path.join(SRC_DIR, manifest)
            dst_m = os.path.join(BRAND_AUDIT_AGENTS, manifest)
            if os.path.exists(src_m):
                shutil.copy2(src_m, dst_m)

    print("=== Synchronization Complete ===")


if __name__ == "__main__":
    main()
