#!/usr/bin/env bash
# Build one tree species (species/<id>.json): inputs -> leaf atlas -> tree (clumps, occlusion COLOR_0, LOD subsets)
# -> LOD2 clump cards -> [fruit] -> impostor -> far maps to 512² -> export -> link + validate [--install] -> review sheets.
# A species with "base" (the fruit-bearing food tree) reuses that species' built tree and only adds its fruit.
# MM7 trees_a copy of ../../mm6_new_sorpigal_3d/trees/build.sh.
# Usage: build.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here/scripts"
base=$(python3 -c "import common; print(common.load('$id')['base'] or '')")
if [[ -z "$base" ]]; then
  python3 prepare.py "$id" | grep -E "BARK"
  python3 make_leaf_atlas.py "$id"
  "$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "BARK|CLUMPS|CARDS|OCCLUSION|LEAVES|^LOD|Error|Traceback"
  # lod.lod2 'subset' (MM7 frond conifers): LOD2 keeps a frond subset like LOD1, no clump cards
  if [[ "$(python3 -c "import common; print(common.load('$id')['lod'].get('lod2', 'clumps'))")" != subset ]]; then
    "$blender" --background --python clump_cards.py -- "$id" 2>&1 | grep -E "CLUMP|Error|Traceback"
    python3 make_clump_atlas.py "$id"
    "$blender" --background --python clump_lod2.py -- "$id" 2>&1 | grep -E "LOD2|Error|Traceback"
  fi
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
python3 review_sheet.py "$id"
