#!/usr/bin/env bash
set -euo pipefail
ship_project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ship_project/run_test.py" "$@"
