#!/usr/bin/env bash
set -euo pipefail
viewer_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$viewer_dir/serve.py" "$@"
