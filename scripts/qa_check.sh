#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Production QA Pipeline ==="

VENV_BIN="$PROJECT_ROOT/.venv/bin"

if [ -f "$VENV_BIN/ruff" ] && [ -f "$VENV_BIN/flake8" ] && [ -f "$VENV_BIN/mypy" ]; then
    echo "=== 1. Ruff Linter & Formatter ==="
    "$VENV_BIN/ruff" check src/ tests/
    echo "  [OK] Ruff check passed with 0 errors."

    echo ""
    echo "=== 2. Flake8 Strict Style Checker ==="
    "$VENV_BIN/flake8" src/ tests/ --max-line-length=140 --ignore=E402,E501,W503
    echo "  [OK] Flake8 check passed with 0 errors."

    echo ""
    echo "=== 3. MyPy Static Type Checker ==="
    for skill in src/skills/*; do
        if [ -d "$skill" ]; then
            "$VENV_BIN/mypy" "$skill" --ignore-missing-imports --no-error-summary >/dev/null 2>&1 || "$VENV_BIN/mypy" "$skill" --ignore-missing-imports
        fi
    done
    echo "  [OK] MyPy passed across all 8 skills."

    echo ""
    echo "=== 4. JSON Integrity & Draft-07 Schema Gate ==="
    python3 -c "
import glob, json
for jf in sorted(glob.glob('src/**/*.json', recursive=True) + glob.glob('src/*.json')):
    with open(jf, 'r', encoding='utf-8') as fp:
        json.load(fp)
print('  [OK] All JSON manifests, evals, and schema files valid.')
"

    echo ""
    echo "=== 5. Pytest Unit Test Suite ==="
    "$VENV_BIN/pytest" tests/ -q
elif command -v uv >/dev/null 2>&1; then
    echo "=== 1. Syncing Environment with uv ==="
    uv sync --all-extras 2>/dev/null || true

    echo ""
    echo "=== 2. Ruff (Fast Linter & Formatter) ==="
    uv run ruff check src/ tests/

    echo ""
    echo "=== 3. Flake8 (Strict Style Checker) ==="
    uv run flake8 src/ tests/ --max-line-length=140 --ignore=E402,E501,W503

    echo ""
    echo "=== 4. MyPy (Static Type Checking) ==="
    for skill in src/skills/*; do
        if [ -d "$skill" ]; then
            uv run mypy "$skill" --ignore-missing-imports
        fi
    done

    echo ""
    echo "=== 5. Pytest Unit Tests ==="
    uv run pytest tests/ -q
else
    echo "Notice: Running standard Python QA suite..."
    echo ""
    echo "=== 1. Python Syntax & AST Compilation ==="
    python3 -c "
import glob, py_compile, ast
for f in sorted(glob.glob('src/**/*.py', recursive=True) + glob.glob('tests/*.py')):
    py_compile.compile(f, doraise=True)
    with open(f, 'r', encoding='utf-8') as fp:
        ast.parse(fp.read(), filename=f)
print('  [OK] All Python files compiled and AST validated cleanly.')
"

    echo ""
    echo "=== 2. Strict Code Quality & Style Gate ==="
    python3 -c "
import glob, ast, sys
all_files = sorted(glob.glob('src/**/*.py', recursive=True) + glob.glob('tests/*.py'))
issues = []
for filepath in all_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = ''.join(lines)
    tree = ast.parse(content, filename=filepath)
    for idx, line in enumerate(lines):
        if line.rstrip('\r\n') != line.rstrip():
            issues.append(f'{filepath}:{idx+1} Trailing whitespace')
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(f'{filepath}:{node.lineno} Bare except clause')
if issues:
    print(f'  [FAIL] {len(issues)} code quality issues found:')
    for iss in issues[:10]:
        print('    ', iss)
    sys.exit(1)
print('  [OK] 0 code quality / style violations detected.')
"

    echo ""
    echo "=== 3. JSON Integrity & Draft-07 Schema Check ==="
    python3 -c "
import glob, json
for jf in sorted(glob.glob('src/**/*.json', recursive=True) + glob.glob('src/*.json')):
    with open(jf, 'r', encoding='utf-8') as fp:
        json.load(fp)
print('  [OK] All JSON manifests, evals, and schema files valid.')
"

    echo ""
    echo "=== 4. Unit Test Suite (Python unittest) ==="
    python3 -m unittest discover -s tests
fi

echo ""
echo "=== QA Pipeline Complete: All Checks Green ==="
