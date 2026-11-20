#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (Mummy copy of the Zombie's): swap_mp (index buffers into the installed LOD0, every vertex
# attribute exact) -> build_lods.py (tools/build_actor_lods.py, default ratios, 4 influences, protected soles/top/corpse points
# snapped to the import) -> the creature's shrink_shadow_lods (../mm9_skeletonwarrior_claude, as rebuild.sh) -> carry_variants
# (the creature's tier_skins variants onto every LOD and shadow primitive) -> check_winding. Clips (floor-fixed, mirrored),
# materials, variants and images stay the installed ones.
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r62> [out glb, default export/mm9_mummy_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
o=work/b_$tag; OUT=${2:-export/mm9_mummy_$tag.glb}; mkdir -p "$(dirname $OUT)"
$G scripts/swap_mp.py before/mm9_mummy.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb $OUT Mummy 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py $OUT 2>&1 | grep -v Unexpected
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
