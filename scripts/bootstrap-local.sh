#!/usr/bin/env bash
# One-time local env bootstrap. Safe to re-run; does not overwrite existing files.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BE="$ROOT/backend/.env"
FE="$ROOT/frontend/.env.local"
if [[ ! -f "$BE" ]]; then
  cp "$ROOT/backend/.env.example" "$BE"
  echo "Created backend/.env from .env.example"
else
  echo "backend/.env already exists — skipped"
fi
if [[ ! -f "$FE" ]]; then
  cp "$ROOT/frontend/.env.example" "$FE"
  echo "Created frontend/.env.local from .env.example"
else
  echo "frontend/.env.local already exists — skipped"
fi
echo "Next: see docs/SETUP.md and README.md (Run locally)."
