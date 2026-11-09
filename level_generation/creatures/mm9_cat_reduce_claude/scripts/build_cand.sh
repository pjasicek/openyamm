#!/usr/bin/env bash
# Candidate runtime GLB from one mpqem step: swap_mp.py (LOD0 index buffer only, every vertex an installed one) ->
# build_lods.py (snap-fixed protected points, the tool's 0.5/0.18/0.06 as the cat was built) -> shrink_shadow_lods.py (the cat project's own copy, wolf margins; as
# ../mm9_cat_claude/scripts/build_runtime.sh) -> carry_variants.py -> UV chart audit (hard gate), same_clips, winding, LOD check.
# Clips are byte-identical, so the cat floor pass (floor_smooth.py) is not re-run. Usage: scripts/build_cand.sh <label_rNN>  -> export/cand_<label_rNN>/mm9_cat.glb
set -euo pipefail
cd "$(dirname "$0")/.."
t=$1; o=export/cand_$t; mkdir -p $o
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/swap_mp.py before/mm9_cat.glb work/mp_$t.npz $o/lod0.glb 2>&1 | grep -v RuntimeWarning
$BL -P scripts/build_lods.py -- $o/lod0.glb $o/lods.glb 2>&1 | grep -E "PROTECTED|LOD triangles|Error|Traceback"
$G scripts/shrink_shadow_lods.py $o/lods.glb $o/shadow.glb Cat 2>&1 | grep -v RuntimeWarning | tail -3
cp $o/shadow.glb $o/mm9_cat.glb
$G scripts/carry_variants.py $o/mm9_cat.glb 2>&1 | grep -v RuntimeWarning
$G ../claude_shared/reduction_uv_audit.py $o/mm9_cat.glb before/mm9_cat.glb --json review/uv_audit_$t.json 2>&1 | grep -v RuntimeWarning | tail -8
$G scripts/same_clips.py before/mm9_cat.glb $o/mm9_cat.glb 2>&1 | grep -v RuntimeWarning | tail -3
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $o/mm9_cat.glb 2>&1 | grep -v RuntimeWarning | tail -1
sha256sum $o/mm9_cat.glb
