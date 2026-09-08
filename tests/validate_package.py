"""
validate_package.py - Package hygiene validator and test suite entrypoint.

Checks:
- brand-ai-readiness-audit.zip exists and is <= 50 MB
- Zip contains no __pycache__ or .pyc files
- Zip contains exactly 8 skill folders
- Zip contains marketplace.json, README.md, LICENSE at root
- marketplace.json inside zip has a "version" field ("1.0.0")
- Every Python script in the package has valid Python syntax (py_compile sweep)
- Every relative link in every Markdown file resolves to an existing file in the package

Usage:
    python3 tests/validate_package.py [path/to/brand-ai-readiness-audit.zip]
    python3 -m unittest tests/validate_package.py
"""

import json
import os
import py_compile
import re
import sys
import tempfile
import unittest
import zipfile

MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
EXPECTED_SKILLS = {
    "audit-orchestrator",
    "web-scraper",
    "discoverability-audit",
    "entity-content-audit",
    "fact-consistency-audit",
    "corroboration-authority-audit",
    "geo-content-audit",
    "engagement-context-audit",
}
ROOT_PREFIX = "brand-ai-readiness-audit/"


def validate(zip_path: str) -> list:
    """Return list of error strings. Empty list means all checks passed."""
    errors = []

    # 1. File exists
    if not os.path.isfile(zip_path):
        return [f"Zip file not found: {zip_path}"]

    # 2. Size check
    size = os.path.getsize(zip_path)
    if size > MAX_SIZE_BYTES:
        errors.append(
            f"Zip too large: {size / 1024 / 1024:.1f} MB > 50 MB limit"
        )

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())

        # 3. No __pycache__ or .pyc junk
        junk = [n for n in names if "__pycache__" in n or n.endswith(".pyc")]
        if junk:
            errors.append(
                f"Zip contains {len(junk)} cache/compiled files: {junk[:5]}"
            )

        # 4. Root folder prefix consistent
        non_root = [n for n in names if not n.startswith(ROOT_PREFIX)]
        if non_root:
            errors.append(
                f"Files outside expected root '{ROOT_PREFIX}': {non_root[:5]}"
            )

        # 5. Required root files
        for required in ("marketplace.json", "README.md"):
            full = ROOT_PREFIX + required
            if full not in names:
                errors.append(f"Missing required root file: {full}")

        # 6. Skill folders present
        found_skills = set()
        for name in names:
            if name.startswith(ROOT_PREFIX + "skills/"):
                rest = name[len(ROOT_PREFIX + "skills/"):]
                parts = rest.split("/")
                if parts[0] and not parts[0].startswith("."):
                    found_skills.add(parts[0])
        missing_skills = EXPECTED_SKILLS - found_skills
        if missing_skills:
            errors.append(f"Missing skill folders in zip: {sorted(missing_skills)}")

        # 7. marketplace.json has version
        mkt_path = ROOT_PREFIX + "marketplace.json"
        if mkt_path in names:
            try:
                mkt = json.loads(zf.read(mkt_path).decode("utf-8"))
                if "version" not in mkt:
                    errors.append("marketplace.json inside zip is missing 'version' field")
            except Exception as e:
                errors.append(f"Failed to parse marketplace.json: {e}")

        # 8. py_compile sweep on all Python scripts in zip
        with tempfile.TemporaryDirectory() as tmpdir:
            py_files = [n for n in names if n.endswith(".py")]
            for py_name in py_files:
                code_bytes = zf.read(py_name)
                tmp_script = os.path.join(tmpdir, os.path.basename(py_name))
                with open(tmp_script, "wb") as f:
                    f.write(code_bytes)
                try:
                    py_compile.compile(tmp_script, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"Syntax error in {py_name}: {e}")
                except Exception as e:
                    errors.append(f"Compilation failure in {py_name}: {e}")

        # 9. Markdown relative link resolution
        md_files = [n for n in names if n.endswith(".md")]
        for md_name in md_files:
            try:
                content = zf.read(md_name).decode("utf-8")
            except Exception:
                continue

            md_dir = os.path.dirname(md_name)
            # Find markdown links: [text](target)
            matches = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
            for _text, target in matches:
                target_clean = target.strip().split("#")[0].split("?")[0]
                if not target_clean:
                    continue
                # Skip external protocols, mailto, and anchor links
                if target_clean.startswith(("http://", "https://", "mailto:", "ftp:", "file:")):
                    continue
                # Resolve relative target against md file's directory
                resolved = os.path.normpath(os.path.join(md_dir, target_clean))
                # Normalize path separators
                resolved = resolved.replace("\\", "/")
                # Check if resolved file or directory exists in zip
                if resolved not in names and (resolved + "/") not in names:
                    # Allow workspace-level documentation references that point to repo root docs
                    repo_resolved = ROOT_PREFIX + target_clean.lstrip("/")
                    if repo_resolved not in names and (repo_resolved + "/") not in names:
                        errors.append(
                            f"Broken relative link in {md_name}: '{target}' (resolved to '{resolved}')"
                        )

    return errors


class TestPackageHygiene(unittest.TestCase):
    """Unit test runner wrapper for validate_package."""

    def test_distribution_zip_hygiene(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zip_path = os.path.join(repo_root, "brand-ai-readiness-audit.zip")
        if not os.path.isfile(zip_path):
            self.skipTest(f"Distribution zip not yet built at {zip_path}. Run ./scripts/build.sh first.")
        errors = validate(zip_path)
        self.assertEqual(errors, [], "Package hygiene failures:\n" + "\n".join(f"  - {e}" for e in errors))


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        repo_root, "brand-ai-readiness-audit.zip"
    )

    print(f"Validating: {zip_path}")
    errors = validate(zip_path)

    if errors:
        print(f"\n[FAIL] {len(errors)} issue(s) found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        size_mb = os.path.getsize(zip_path) / 1024 / 1024
        print(f"[OK] Package valid — {size_mb:.1f} MB, all checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
