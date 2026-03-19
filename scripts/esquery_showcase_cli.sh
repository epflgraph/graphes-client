#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Running ESQuery showcase..."
python3 "${ROOT_DIR}/scripts/esquery_showcase.py"
