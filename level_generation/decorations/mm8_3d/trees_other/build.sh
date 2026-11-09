#!/usr/bin/env bash
# Build one MM8 trees_other species (species/<id>.json) with the shared textures (shared/, scripts/make_shared.py):
#   conifer: envelope -> whorls of spray cards (conifer_build.py) -> impostor -> export -> link + validate -> review
#   sculpt:  hand-authored limbs + foliage pads (sculpt_build.py) -> impostor -> export -> ...
#   clump:   envelope -> Sapling tree with clumps (build_tree.py) -> LOD2 clump cards -> impostor -> export -> ...
# [--install] installs through tools/install_model.py --engine. Dead trees: scripts/dead_build.sh.
# Usage: build.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here/scripts"
kind=$(python3 -c "import common; print(common.load('$id')['kind'])")
python3 prepare.py "$id"
if [[ "$kind" == conifer ]]; then
  "$blender" --background --python conifer_build.py -- "$id" 2>&1 | grep -E "TINT|BRANCHES|CARDS|OCCLUSION|LEAVES|BARK|^LOD|Error|Traceback"
elif [[ "$kind" == sculpt ]]; then
  "$blender" --background --python sculpt_build.py -- "$id" 2>&1 | grep -E "TINT|LIMBS|PADS|CARDS|OCCLUSION|LEAVES|BARK|^LOD|Error|Traceback"
else
  "$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "TINT|BARK|CLUMPS|CARDS|OCCLUSION|LEAVES|^LOD|Error|Traceback"
  "$blender" --background --python clump_cards.py -- "$id" 2>&1 | grep -E "CLUMP|Error|Traceback"
  python3 make_clump_atlas.py "$id"
  "$blender" --background --python clump_lod2.py -- "$id" 2>&1 | grep -E "LOD2|Error|Traceback"
fi
"$blender" --background --python bake_impostor.py -- "$id" 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
python3 finish_impostor.py "$id"
python3 shrink_far_maps.py "$id"
"$blender" --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 post_process.py "$id" "$@" | tee "../work/$id/validation.txt"
python3 review.py "$id"
python3 lod_check.py "$id"
python3 stack_sheet.py "$id"
