#!/bin/bash
# seed_products.sh - Reusable catalog seeding command for SmartCart AI.
#
# Downloads open/licensed product data (Open Food Facts, Open Beauty Facts,
# Open Pet Food Facts, Wikimedia Commons) + images, validates, normalizes and
# idempotently inserts into PostgreSQL.
#
# Usage:
#   ./seed_products.sh                 # full seed
#   ./seed_products.sh --refresh       # re-fetch raw candidates
#   ./seed_products.sh --category Fruits
#   ./seed_products.sh --limit 20      # smoke test
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/backend" && pwd)"
cd "$BACKEND_DIR"

VENV="$BACKEND_DIR/.venv"
if [ -x "$VENV/bin/python" ]; then
  PY="$VENV/bin/python"
else
  PY="python3"
fi

echo ">>> SmartCart AI - product catalog seeder"
echo ">>> backend: $BACKEND_DIR"
exec "$PY" -m seed run "$@"
