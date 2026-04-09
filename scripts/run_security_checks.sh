#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
  echo "Virtual environment not found at backend/venv"
  echo "Create it first: python -m venv venv && source venv/bin/activate"
  exit 1
fi

source venv/bin/activate

echo "[1/3] Running Bandit security scan..."
bandit -r app utils -q

echo "[2/3] Running Safety dependency scan..."
safety check -r requirements.txt || true

echo "[3/3] Running focused auth smoke checks..."
pytest tests/test_auth.py -q || true

echo "Security checks completed. Review output for findings."
