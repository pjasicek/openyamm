#!/usr/bin/env bash
# PeasantF2: pose-aware step -> runtime candidate: swap_mp (index buffers into the installed LOD0, every vertex attribute
# exact) -> the model's own LOD chain (build_runtime.sh: tools/build_actor_lods.py with 4 influences, here with protected
# points -> mm9_skeletonwarrior's shrink_shadow_lods -> carry_variants -> the creature's fix_winding) -> check_winding.
# The head set is made single-sided for the LOD builder and doubleSided again after it (as build_runtime.sh).
# Clips, materials (doubleSided head set), variants, ramps and images stay the installed ones.
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_b_r40> [out glb, default export/mm9_peasantf2_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
o=work/b_$tag; OUT=${2:-export/mm9_peasantf2_$tag.glb}
$G scripts/swap_mp.py before/mm9_peasantf2.glb work/$tag.npz ${o}_lod0d.glb 2>&1 | grep -v Unexpected
$G scripts/single_head.py ${o}_lod0d.glb ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb PeasantF2 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G ../mm9_peasantf2_claude/scripts/double_head.py ${o}_sf.glb ${o}_sfd.glb 2>&1 | grep -v Unexpected
$G ../mm9_peasantf2_claude/scripts/fix_winding.py ${o}_sfd.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
