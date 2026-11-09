#!/usr/bin/env bash
# Review renders and sheets of the hanged corpses: review/<corpse>/compare.png. Usage: review_hanged.sh <corpse>...
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
for c in "$@"; do
  /snap/bin/blender --background --python scripts/review.py -- "$c" "work/${c}_export.glb" 0 4 2>&1 | grep -E "Error|Traceback" || true
  python3 scripts/sheet.py "$c" "${c}_p143.png"
done
