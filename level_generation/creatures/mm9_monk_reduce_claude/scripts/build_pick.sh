#!/usr/bin/env bash
# Picked ladder step -> runtime candidate, the Monk's own LOD chain (../mm9_monk_claude/scripts/rebuild.sh after the clips).
# Usage (any folder): build_pick.sh <ladder label> <tag, e.g. r76> [final]
#  work/<label>_<tag>_lod0.glb: export_cand (floor = source's lowest point) -> swap_lod0 into the installed source
#  (materials, variants, tier heads, floor-fixed clips, sockets stay byte for byte) -> fix_normals (installed normals on
#  source vertices, build_glb's rule on new ones, MonkHead primitive restored byte for byte).
#  With "final": tools/build_actor_lods.py (default ratios, 4 influences) -> shrink_shadow_lods -> carry_variants ->
#  the Monk's LOD winding fix -> $OUT (default export/mm9_monk.glb), then check_winding.
set -euo pipefail
label=$1; tag=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
o=work/${label}_${tag}; OUT=${OUT:-export/mm9_monk.glb}
REA_BLEND=ladder_$label.blend REA_CAND=Cand_${tag#r} REA_NODE=Monk REA_OUT=${label}_${tag}_cand.glb $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
$G scripts/swap_lod0.py before/mm9_monk.glb ${o}_cand.glb ${o}_swap.glb Monk 2>&1 | grep -v Unexpected
$G scripts/fix_normals.py before/mm9_monk.glb ${o}_swap.glb ${o}_lod0.glb 2>&1 | grep -v Unexpected
[ "${3:-}" == final ] || exit 0
$BL --disable-autoexec --python "$R/tools/build_actor_lods.py" -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" --mesh-node Monk --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Monk 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G ../mm9_monk_claude/scripts/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
