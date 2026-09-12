"""
test_marketplace.py - Manifest integrity and check ownership validation.

Validates:
- marketplace.json has a "version" field
- All skill IDs in marketplace.json have a corresponding folder in skills/
- Each skill folder has SKILL.md with YAML frontmatter containing name + description
- All 134 check_id values in checks.json are unique (no duplicates/orphans)
- Every "owner" in checks.json matches a real skill ID in marketplace.json
"""
import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
MARKETPLACE_PATH = os.path.join(SRC_ROOT, "marketplace.json")
CHECKS_PATH = os.path.join(
    SRC_ROOT, "skills", "audit-orchestrator", "references", "checks.json"
)
SKILLS_DIR = os.path.join(SRC_ROOT, "skills")


def _load_marketplace():
    with open(MARKETPLACE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_checks():
    with open(CHECKS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _skill_ids(marketplace):
    return {s["id"] for s in marketplace.get("skills", [])}


class TestMarketplaceVersion(unittest.TestCase):
    def test_version_field_present(self):
        mkt = _load_marketplace()
        self.assertIn("version", mkt, "marketplace.json is missing a 'version' field")
        self.assertIsInstance(mkt["version"], str)
        self.assertGreater(len(mkt["version"]), 0)


class TestSkillFolderParity(unittest.TestCase):
    def test_all_skill_ids_have_folders(self):
        mkt = _load_marketplace()
        missing = []
        for skill in mkt.get("skills", []):
            skill_id = skill["id"]
            folder = os.path.join(SKILLS_DIR, skill_id)
            if not os.path.isdir(folder):
                missing.append(skill_id)
        self.assertEqual(missing, [], f"Skill IDs with no matching folder: {missing}")

    def test_skill_folders_have_skill_md(self):
        mkt = _load_marketplace()
        missing_md = []
        for skill in mkt.get("skills", []):
            skill_id = skill["id"]
            skill_md = os.path.join(SKILLS_DIR, skill_id, "SKILL.md")
            if not os.path.isfile(skill_md):
                missing_md.append(skill_id)
        self.assertEqual(missing_md, [], f"Skills missing SKILL.md: {missing_md}")

    def test_skill_md_has_frontmatter(self):
        """Each SKILL.md must have YAML frontmatter with name and description."""
        mkt = _load_marketplace()
        problems = []
        for skill in mkt.get("skills", []):
            skill_id = skill["id"]
            skill_md = os.path.join(SKILLS_DIR, skill_id, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            with open(skill_md, encoding="utf-8") as f:
                content = f.read()
            if not content.startswith("---"):
                problems.append(f"{skill_id}: SKILL.md missing YAML frontmatter")
                continue
            front_end = content.find("---", 3)
            frontmatter = content[3:front_end] if front_end > 3 else ""
            if "name:" not in frontmatter:
                problems.append(f"{skill_id}: frontmatter missing 'name:'")
            if "description:" not in frontmatter:
                problems.append(f"{skill_id}: frontmatter missing 'description:'")
            if "compatibility:" not in frontmatter:
                problems.append(f"{skill_id}: frontmatter missing 'compatibility:'")
            if "allowed-tools:" not in frontmatter:
                problems.append(f"{skill_id}: frontmatter missing 'allowed-tools:'")
        self.assertEqual(problems, [], "\n".join(problems))


class TestChecksIntegrity(unittest.TestCase):
    VALID_CATEGORIES = {
        "technical",
        "content",
        "website-type",
        "off-site",
        "bridge",
        "engagement",
    }

    def test_no_duplicate_check_ids(self):
        checks = _load_checks()
        from collections import Counter
        counts = Counter(c.get("check_id", "") for c in checks)
        duplicates = {cid: n for cid, n in counts.items() if n > 1}
        self.assertEqual(duplicates, {}, f"Duplicate check_ids: {duplicates}")

    def test_all_owners_are_valid_skill_ids(self):
        mkt = _load_marketplace()
        valid_ids = _skill_ids(mkt)
        checks = _load_checks()
        stale = [
            (c.get("check_id", "?"), c.get("owner", ""))
            for c in checks
            if c.get("owner", "") not in valid_ids
        ]
        self.assertEqual(
            stale, [],
            "Checks with owner not in marketplace.json:\n"
            + "\n".join(f"  {cid}: {owner}" for cid, owner in stale),
        )

    def test_all_categories_valid(self):
        checks = _load_checks()
        invalid = [
            (c.get("check_id", "?"), c.get("category", "<missing>"))
            for c in checks
            if c.get("category") not in self.VALID_CATEGORIES
        ]
        self.assertEqual(
            invalid, [],
            f"Checks with invalid or missing category (must be one of {sorted(self.VALID_CATEGORIES)}):\n"
            + "\n".join(f"  {cid}: {cat}" for cid, cat in invalid),
        )

    def test_check_count(self):
        checks = _load_checks()
        self.assertEqual(len(checks), 134, f"Expected 134 checks, found {len(checks)}")

    def test_all_checks_have_required_fields(self):
        checks = _load_checks()
        required = {"check_id", "owner", "category", "title"}
        problems = []
        for c in checks:
            missing = required - set(c.keys())
            if missing:
                problems.append(f"  check_id={c.get('check_id', '?')}: missing {missing}")
        self.assertEqual(problems, [], "Checks missing required fields:\n" + "\n".join(problems))

    def test_checks_cross_reference_join(self):
        """Assert zero orphan check IDs between checks.json and checks.md reference files."""
        import glob
        import re
        checks = _load_checks()
        json_ids = {c["check_id"] for c in checks}

        md_files = glob.glob(
            os.path.join(SKILLS_DIR, "**", "references", "checks.md"),
            recursive=True,
        )
        self.assertGreater(len(md_files), 0, "No checks.md reference files found")

        md_ids = set()
        for md_path in md_files:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            found = re.findall(r"^##\s+([A-Za-z0-9_]+)", content, re.MULTILINE)
            found = [x for x in found if x not in {"Table", "Contents"}]
            md_ids.update(found)

        orphans_in_json = json_ids - md_ids
        orphans_in_md = md_ids - json_ids
        self.assertEqual(
            orphans_in_json, set(),
            f"Check IDs in checks.json but missing from checks.md reference files: {sorted(orphans_in_json)}",
        )
        self.assertEqual(
            orphans_in_md, set(),
            f"Check IDs in checks.md reference files but missing from checks.json: {sorted(orphans_in_md)}",
        )


if __name__ == "__main__":
    unittest.main()
