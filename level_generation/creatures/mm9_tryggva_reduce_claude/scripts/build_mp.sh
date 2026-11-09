#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (PeasantM1 reduce project's build_mp.sh adapted): swap_mp (index buffers into the
# installed LOD0, every vertex attribute exact) -> build_lods.py (tools/build_actor_lods.py, 0.5/0.18/0.06, 4 influences, soles,
# crown and corpse contact protected and snapped) -> the creature's own shrink_shadow_lods.py (../mm9_tryggva_claude/scripts, read in place)
# -> PeasantM1d's fix_winding.py (../mm9_peasantm1d_claude/scripts, same mirrored chain, read in place) -> check_winding.
# One skin, no variants (carry_variants not needed). Clips (floor-fixed), materials and images stay the installed ones.
# Usage (project folder): build_mp.sh <mp npz under work/, e.g. mp_a_r75> [out glb, default export/mm9_tryggva_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_peasantm1d_claude; H1=../mm9_tryggva_claude; o=work/b_$tag; OUT=${2:-export/mm9_tryggva_$tag.glb}
mkdir -p export
$G scripts/swap_mp.py before/mm9_tryggva.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G $H1/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Tryggva 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G $H/scripts/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
