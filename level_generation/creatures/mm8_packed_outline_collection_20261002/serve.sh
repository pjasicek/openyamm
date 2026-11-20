#!/usr/bin/env bash
set -euo pipefail
staging_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd -- "$staging_dir/../../.." && pwd)"
exec python3 -B "$repository_root/level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py" \
  --collection "$staging_dir/collection.json" \
  --state-dir "$staging_dir/review_state" \
  --port "${1:-8768}"
