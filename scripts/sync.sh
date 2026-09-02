#!/bin/bash
set -e
echo "Syncing skills to .agents/skills..."
mkdir -p .agents/skills
rsync -av --delete --exclude '__pycache__' src/skills/ .agents/skills/
echo "Sync complete."
