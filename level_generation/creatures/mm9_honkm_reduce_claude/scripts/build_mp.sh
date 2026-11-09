#!/usr/bin/env bash
# Pose-aware step -> runtime candidate: swap_mp (index buffers into the installed LOD0, every vertex attribute exact) ->
# build_lods.py (tools/build_actor_lods.py defaults, protected points snapped to the import) -> the Honk's own
# shrink_shadow_lods -> carry_variants -> check_winding. Clips, materials, variants and images stay the installed ones.
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r60> [out glb, default export/mm9_honkm_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_honkmale_claude/v2/scripts; o=work/b_$tag; OUT=${2:-export/mm9_honkm_$tag.glb}
$G scripts/swap_mp.py before/mm9_honkm.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G $H/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb HonkM 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
cp ${o}_sf.glb $OUT
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
