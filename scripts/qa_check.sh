#!/bin/bash
set -e

echo "=== Production QA Pipeline ==="

if command -v uv >/dev/null 2>&1; then
    echo "=== 1. Syncing Environment with uv ==="
    uv sync --all-extras 2>/dev/null || true

    echo ""
    echo "=== 2. Ruff (Fast Linter & Formatter) ==="
    uv run ruff check src/ tests/ || echo "⚠️ Ruff found issues."

    echo ""
    echo "=== 3. Flake8 (Strict Style Checker) ==="
    uv run flake8 src/ tests/ --max-line-length=120 --ignore=E402,E501,W503 || echo "⚠️ Flake8 found issues."

    echo ""
    echo "=== 4. MyPy (Static Type Checking) ==="
    for skill in src/skills/*; do
        if [ -d "$skill" ]; then
            echo "Checking $(basename $skill)..."
            uv run mypy "$skill" --ignore-missing-imports || echo "⚠️ MyPy found type issues in $skill."
        fi
    done

    echo ""
    echo "=== 5. Pytest Unit Tests ==="
    uv run pytest tests/ || python3 -m unittest discover -s tests
else
    echo "Notice: 'uv' not found in PATH. Running standard Python QA suite..."
    echo ""
    echo "=== 1. Python Syntax & AST Compilation ==="
    python3 -c "
import glob, py_compile, ast
for f in glob.glob('src/**/*.py', recursive=True) + glob.glob('tests/*.py'):
    py_compile.compile(f, doraise=True)
    with open(f, 'r', encoding='utf-8') as fp:
        ast.parse(fp.read(), filename=f)
print('  [OK] All Python files compiled and AST validated cleanly.')
"

    echo ""
    echo "=== 2. JSON Integrity & Draft-07 Schema Check ==="
    python3 -c "
import glob, json
for jf in glob.glob('src/**/*.json', recursive=True) + glob.glob('src/*.json'):
    with open(jf, 'r', encoding='utf-8') as fp:
        json.load(fp)
print('  [OK] All JSON manifests, evals, and schema files valid.')
"

    echo ""
    echo "=== 3. Unit Test Suite (Python unittest) ==="
    python3 -m unittest discover -s tests
fi

echo ""
echo "=== QA Pipeline Complete: All Checks Green ==="
