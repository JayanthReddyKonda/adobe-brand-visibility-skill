"""Portable package validation for brand-ai-readiness-audit marketplace.
Supports validating the src directory, build directory, or distribution zip.
"""
import json
import re
import sys
import zipfile
from pathlib import Path


def validate_extracted_tree(root: Path):
    root = root.resolve()
    manifest_path = root / 'marketplace.json'
    assert manifest_path.exists(), f"marketplace.json missing at {manifest_path}"
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

    assert 'name' in manifest and manifest['name'] == 'brand-ai-readiness-audit'
    assert 'skills' in manifest and isinstance(manifest['skills'], list)
    assert sum(s.get('entrypoint') is True for s in manifest['skills']) == 1, "Exactly one entrypoint required"
    assert len({s['id'] for s in manifest['skills']}) == len(manifest['skills']), "Duplicate skill ID found"

    skills_dir = root / 'skills'
    assert skills_dir.is_dir(), f"skills directory missing at {skills_dir}"
    skill_folders = {str(p.relative_to(root)).replace('\\', '/') for p in skills_dir.iterdir() if p.is_dir()}
    manifest_paths = {s['path'] for s in manifest['skills']}
    assert manifest_paths == skill_folders, f"Manifest paths {manifest_paths} != folders {skill_folders}"

    for skill in manifest['skills']:
        directory = (root / skill['path']).resolve()
        assert directory.is_relative_to(root), f"Path escape in {skill}"
        skill_md = directory / 'SKILL.md'
        assert skill_md.exists(), f"SKILL.md missing in {directory}"
        text = skill_md.read_text(encoding='utf-8')
        assert text.startswith('---\n'), f"{skill_md} missing leading frontmatter delimiter"

        parts = text.split('---', 2)
        assert len(parts) >= 3, f"{skill_md} invalid frontmatter format"
        frontmatter_raw = parts[1].strip()

        # Parse top-level keys in frontmatter
        fields = {}
        for line in frontmatter_raw.splitlines():
            if ': ' in line and not line.startswith(' ') and not line.startswith('\t'):
                k, v = line.split(': ', 1)
                fields[k.strip()] = v.strip().strip('"').strip("'")
            elif line.endswith(':') and not line.startswith(' ') and not line.startswith('\t'):
                fields[line[:-1].strip()] = True

        assert fields.get('name') == directory.name == skill['id'], f"Skill name mismatch: {fields.get('name')} vs {directory.name}"
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', fields['name']) and len(fields['name']) <= 64
        assert 'description' in fields and 1 <= len(fields['description']) <= 1024, f"Description length invalid in {skill['id']}"
        assert len(fields.get('compatibility', '')) <= 500, f"Compatibility length invalid in {skill['id']}"
        assert 'allowed-tools' in fields, f"allowed-tools missing in {skill['id']}"
        assert len(text.splitlines()) < 500, f"{skill_md} exceeds 500 line ceiling ({len(text.splitlines())} lines)"

        # Validate relative markdown links
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target_path = target.split('#')[0]
            if target_path and '://' not in target_path and not target_path.startswith('mailto:'):
                resolved = (directory / target_path).resolve()
                assert resolved.exists(), f"Broken relative link in {skill['id']}: {target} -> {resolved}"

    checks_path = root / 'skills/audit-orchestrator/references/checks.json'
    assert checks_path.exists(), f"checks.json missing at {checks_path}"
    checks = json.loads(checks_path.read_text(encoding='utf-8'))
    assert len(checks) == len({c['check_id'] for c in checks}) == 134, f"Expected 134 unique checks, got {len(checks)}"
    for c in checks:
        assert all(c.get(k) for k in ('detection', 'activation', 'solution', 'solution_level', 'reference_band')), f"Check {c.get('check_id')} missing required fields"

    total_size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    assert total_size < 50_000_000, f"Uncompressed package exceeds 50 MB: {total_size} bytes"
    return len(manifest['skills']), len(checks), total_size


def validate_zip(zip_path: Path):
    assert zip_path.exists(), f"Zip file missing at {zip_path}"
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Invariant: single root folder
            roots = {p.split('/')[0] for p in z.namelist() if p.strip()}
            assert len(roots) == 1, f"Expected single root in zip, got {roots}"
            root_name = list(roots)[0]
            z.extractall(tmpdir)
        return validate_extracted_tree(Path(tmpdir) / root_name)


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'src'
    if target.suffix == '.zip':
        skills_count, checks_count, total_size = validate_zip(target)
        print(f"Zip validated successfully: single root, {skills_count} skills, {checks_count} checks, {total_size / 1024:.1f} KB uncompressed.")
    elif target.is_dir():
        skills_count, checks_count, total_size = validate_extracted_tree(target)
        print(f"Directory validated successfully: {skills_count} skills, {checks_count} checks, {total_size / 1024:.1f} KB uncompressed.")
    else:
        raise ValueError(f"Invalid target: {target}")


if __name__ == '__main__':
    main()
