#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (PeasantF8's build_mp.sh for the half-orc women, M=1|2): swap_mp (index buffers into the
# installed LOD0, every vertex attribute exact) -> build_lods.py (tools/build_actor_lods.py 0.5/0.18/0.06, 4 influences, soles,
# crown and corpse contact protected and snapped) -> the creature's shrink_shadow_lods.py -> carry_variants -> the creature's
# fix_winding.py -> check_winding. Clips (floor-fixed), materials, variants and images stay the installed ones.
# Usage: M=1 build_mp.sh <mp npz under work/hof$M/, e.g. mp_a_r50> <out glb>
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"; : "${M:?M=1|2}"; export M
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_peasanthof_claude/scripts; o=work/hof$M/b_$tag; OUT=$2
$G scripts/swap_mp.py before/mm9_peasanthof$M.glb work/hof$M/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
flock work/blender.lock $BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G $H/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb PeasantHOF 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G $H/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
