#!/bin/bash
set -e
echo "Cleaning build directory..."
rm -rf build/brand-ai-readiness-audit
mkdir -p build/brand-ai-readiness-audit



echo "Copying src to build..."
cp -a src/* build/brand-ai-readiness-audit/

echo "Removing __pycache__ and .pyc..."
find build/brand-ai-readiness-audit -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find build/brand-ai-readiness-audit -name "*.pyc" -type f -delete 2>/dev/null || true

echo "Creating zip..."
cd build
rm -f brand-ai-readiness-audit.zip
zip -r brand-ai-readiness-audit.zip brand-ai-readiness-audit > /dev/null
cp brand-ai-readiness-audit.zip ../
echo "Build complete."
