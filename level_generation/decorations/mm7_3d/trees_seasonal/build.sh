#!/usr/bin/env bash
# Build one tree species (species/<id>.json): inputs -> leaf atlas -> tree (clumps, occlusion COLOR_0, LOD subsets)
# -> LOD2 clump cards -> [fruit] -> impostor -> far maps to 512² -> export -> link + validate [--install] -> review sheets.
# A species with "base" (the fruit-bearing food tree) reuses that species' built tree and only adds its fruit.
# A bare winter state ("season": "bare") rebuilds its family's skeleton without leaves (bare_prepare.py, bare_build.py).
# Usage: build.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
# MM7 seasonal trees: a seasonal variant ("family") rebuilds its family's skeleton and crown from the same settings
# (deterministic: identical geometry) with its own leaf atlas; "season": "bare" goes to bare_build.sh instead.
id="$1"; shift
cd "$here/scripts"
base=$(python3 -c "import common; print(common.load('$id')['base'] or '')")
season=$(python3 -c "import common; print(common.load('$id')['season'])")
if [[ "$season" == "bare" ]]; then
  python3 prepare.py "$id" | grep -E "BARK"
  python3 bare_prepare.py "$id"
  "$blender" --background --python bare_build.py -- "$id" 2>&1 | grep -E "BARE|^LOD|Error|Traceback"
elif [[ -z "$base" ]]; then
  python3 prepare.py "$id" | grep -E "BARK"
  python3 make_leaf_atlas.py "$id"
  "$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "BARK|CLUMPS|CARDS|OCCLUSION|LEAVES|^LOD|Error|Traceback"
  "$blender" --background --python clump_cards.py -- "$id" 2>&1 | grep -E "CLUMP|Error|Traceback"
  python3 make_clump_atlas.py "$id"
  "$blender" --background --python clump_lod2.py -- "$id" 2>&1 | grep -E "LOD2|Error|Traceback"
else
  python3 copy_base.py "$id"
fi
if python3 -c "import common, sys; sys.exit(0 if common.load('$id')['fruit'] else 1)"; then
  "$blender" --background --python add_fruit.py -- "$id" 2>&1 | grep -E "FRUIT|Error|Traceback"
fi
"$blender" --background --python bake_impostor.py -- "$id" 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
python3 finish_impostor.py "$id"
python3 shrink_far_maps.py "$id"
"$blender" --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 post_process.py "$id" "$@" | tee "../work/$id/validation.txt"
python3 review.py "$id"
python3 lod_check.py "$id"
