#!/usr/bin/env bash
# Fix-pass build (Winged Mutant, after the Dwarf's): chart-guarded mpqem step -> runtime candidate: swap_mp.py (index buffers
# into the installed LOD0; every vertex attribute exact) -> build_lods.py (tools/build_actor_lods.py default ratios, death floor
# contacts protected) -> the creature's shrink_shadow_lods.py (wing shells stay) -> carry_variants -> the creature's
# fix_winding.py -> fix_lod_floor.py -> check_winding -> same_clips -> reduction_uv_audit (hard gate: 0 LOD0 escapes).
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r80> [out glb, default export_mp/mm9_wingedmutant.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
OUT=${2:-export_mp/mm9_wingedmutant.glb}; o=work/b_$tag; mkdir -p "$(dirname $OUT)"
$G scripts/swap_mp.py before/mm9_wingedmutant.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" Wmut 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error|Traceback"
$G scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_shadow.glb Wmut 2>&1 | grep -v Unexpected | tail -1 | cut -c1-160
$G scripts/carry_variants.py ${o}_shadow.glb 2>&1 | grep -v Unexpected
$G scripts/fix_winding.py ${o}_shadow.glb $OUT 2>&1 | grep -v Unexpected | tail -1
scripts/cap.sh python3 scripts/fix_lod_floor.py $OUT
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
$G scripts/same_clips.py before/mm9_wingedmutant.glb $OUT 2>&1 | grep -v Unexpected | tail -1
scripts/cap.sh python3 scripts/same_check.py before/mm9_wingedmutant.glb $OUT | tail -3
scripts/cap.sh python3 ../claude_shared/reduction_uv_audit.py $OUT before/mm9_wingedmutant.glb --json review/uv_audit.json | grep LOD0
ls -la $OUT
