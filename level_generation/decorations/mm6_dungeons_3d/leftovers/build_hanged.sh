#!/usr/bin/env bash
# Rebuild the hanged and hooked corpses (scripts/build_hanged.py): rope texture -> models -> review sheets -> albedo
# check -> finish (link LODs, validate) [--install [--replace-own] copies them to assets_dev/worlds/mm6/models].
# Usage: build_hanged.sh [--install [--replace-own]] [corpse...]   (no names: all seven)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"
flags=(); while [[ "${1:-}" == --* ]]; do flags+=("$1"); shift; done
corpses=("$@"); (( ${#corpses[@]} )) || corpses=(corpse corpse07 corpse08 corpse11 corpse14 corpse15 corpse18)
python3 scripts/make_textures.py
for c in "${corpses[@]}"; do
  /snap/bin/blender --background --python scripts/build_hanged.py -- "$c" > "work/$c.log" 2>&1 &
done
wait
for c in "${corpses[@]}"; do
  grep -E "LEVEL|CUT|Error|Traceback" "work/$c.log" || true
  scripts/review_hanged.sh "$c"
  python3 scripts/finish.py "$c" "${flags[@]}"
done
