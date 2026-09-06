#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Synchronizing Skills and Marketplace Manifests ==="
mkdir -p .agents/skills
rsync -av --delete --exclude '__pycache__' --exclude '*.pyc' src/skills/ .agents/skills/
cp -f src/marketplace.json .agents/marketplace.json
cp -f src/README.md .agents/README.md
cp -f src/LICENSE .agents/LICENSE

if [ -d "build/brand-ai-readiness-audit" ]; then
    echo "Syncing to build/brand-ai-readiness-audit..."
    mkdir -p build/brand-ai-readiness-audit/skills
    rsync -av --delete --exclude '__pycache__' --exclude '*.pyc' src/skills/ build/brand-ai-readiness-audit/skills/
    cp -f src/marketplace.json build/brand-ai-readiness-audit/marketplace.json
    cp -f src/README.md build/brand-ai-readiness-audit/README.md
    cp -f src/LICENSE build/brand-ai-readiness-audit/LICENSE
fi

echo "=== Synchronization Complete ==="
