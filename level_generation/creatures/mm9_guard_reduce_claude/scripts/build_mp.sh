#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (from mm9_highwayman_reduce_claude): swap_mp (index buffers into the installed LOD0, every
# vertex attribute exact) -> build_lods.py (tools/build_actor_lods.py 0.5 / 0.18 / 0.06, 4 influences, soles, crown and corpse
# contact protected) -> the Guard project's shrink_shadow_lods -> carry_variants -> check_winding. Clips (floor-fixed), materials,
# variants and images stay the installed ones; the halberd and plate attachments are unchanged.
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r50> [out glb, default export/mm9_guard_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_guard_claude/scripts; o=work/b_$tag; OUT=${2:-export/mm9_guard_$tag.glb}
$G scripts/swap_mp.py before/mm9_guard.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G $H/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Guard 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
cp ${o}_sf.glb $OUT
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
