#!/usr/bin/env bash
# Build one MM8 broadleaf species (species/<id>.json) with the shared textures (shared/, from scripts/make_shared.py):
# envelope -> tree (clumps, occlusion x species tint in COLOR_0, LOD subsets) -> LOD2 clump cards -> impostor ->
# far maps to 512² -> export -> link + validate [--install via tools/install_model.py] -> review sheets.
# Usage: build.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here/scripts"
[[ -f ../shared/atlas.json ]] || python3 make_shared.py
python3 prepare.py "$id"
if python3 -c "import common, sys; sys.exit(0 if common.load('$id')['crown'].get('moss') else 1)"; then
  python3 make_willow.py "$id"
fi
"$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "TINT|BARK|CLUMPS|CARDS|OCCLUSION|LEAVES|^LOD|Error|Traceback"
"$blender" --background --python clump_cards.py -- "$id" 2>&1 | grep -E "CLUMP|Error|Traceback"
python3 make_clump_atlas.py "$id"
"$blender" --background --python clump_lod2.py -- "$id" 2>&1 | grep -E "LOD2|Error|Traceback"
"$blender" --background --python bake_impostor.py -- "$id" 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
python3 finish_impostor.py "$id"
python3 shrink_far_maps.py "$id"
"$blender" --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 post_process.py "$id" "$@" | tee "../work/$id/validation.txt"
python3 review.py "$id"
python3 lod_check.py "$id"
python3 stack_sheet.py "$id"
