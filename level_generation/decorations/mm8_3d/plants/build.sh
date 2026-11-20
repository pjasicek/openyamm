#!/usr/bin/env bash
# Build one or more plant models: Blender (recipes) -> post.py (link, cut, validate) -> review sheet.
# Usage: ./build.sh <id>... [--install]   (atlases: python3 scripts/make_atlas.py <atlas> first)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"
install=""
ids=()
for a in "$@"; do
  if [[ "$a" == "--install" ]]; then install="--install"; else ids+=("$a"); fi
done
for id in "${ids[@]}"; do
  [[ -f work/$id/sprite.json ]] || python3 scripts/sprite_maps.py "$id"
  /snap/bin/blender --background --python scripts/build.py -- "$id" > "work/$id.log" 2>&1 || { grep -E "Error|Traceback" -A8 "work/$id.log" | head -40; exit 1; }
  grep -E "Traceback" -A10 "work/$id.log" && exit 1
  grep EXPORTED "work/$id.log" | sed 's/.*LOD/LOD/'
  python3 scripts/post.py "$id" $install | grep -E "VALID|INSTALLED" | cut -c1-200
  python3 scripts/sheet.py "$id"
done
