#!/usr/bin/env bash
set -euo pipefail

# ── Spamlyser Pro Development Setup Script ──────────────────────────────
# Run this script after cloning the repository to set up your local
# development environment with all recommended tools.
#
# Usage:
#   bash scripts/setup-hooks.sh
# ──────────────────────────────────────────────────────────────────────────

echo "=== Spamlyser Pro Development Setup ==="

echo ""
echo "1. Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo ""
echo "2. Installing pre-commit hooks..."
pre-commit install --install-hooks
pre-commit run --all-files

echo ""
echo "3. Verifying project setup..."
python -c "from config import ensure_data_dir; ensure_data_dir(); print('Data directory ready')"

echo ""
echo "=== Setup complete! ==="
echo "Run 'make run' to start the Streamlit app."
echo "Run 'make test' to run the test suite."
