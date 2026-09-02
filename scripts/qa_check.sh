#!/bin/bash
set -e

echo "=== 1. Syncing Environment with uv ==="
# Ensure all development dependencies (ruff, mypy, flake8, pytest) are installed
uv sync --all-extras

echo ""
echo "=== 2. Ruff (Fast Linter & Formatter) ==="
echo "Running Ruff checks..."
uv run ruff check src/ tests/ || echo "⚠️ Ruff found issues."

echo ""
echo "=== 3. Flake8 (Strict Style Checker) ==="
echo "Running Flake8..."
uv run flake8 src/ tests/ --max-line-length=120 --ignore=E402,E501,W503 || echo "⚠️ Flake8 found issues."

echo ""
echo "=== 4. MyPy (Static Type Checking) ==="
echo "Running MyPy..."
# Run mypy on each skill individually to avoid duplicate module resolution errors since we embedded dom.py, fetcher.py, telemetry.py
for skill in src/skills/*; do
    echo "Checking $skill..."
    uv run mypy "$skill" --ignore-missing-imports || echo "⚠️ MyPy found type issues in $skill."
done

echo ""
echo "=== 5. Unit Tests ==="
echo "Running Pytest..."
# Point PYTHONPATH to one of the script directories so dom/fetcher/telemetry resolve correctly during tests
export PYTHONPATH=src/skills/audit-orchestrator/scripts
uv run pytest tests/ || echo "⚠️ Unit tests failed."

echo ""
echo "=== QA Pipeline Complete ==="
