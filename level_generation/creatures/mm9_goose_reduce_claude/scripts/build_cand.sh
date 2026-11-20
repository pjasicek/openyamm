#!/usr/bin/env bash
# Goose candidate runtime GLB from one mpqem step (Ram copy): swap_mp.py (LOD0 index buffer only, every vertex an installed one) ->
# build_lods.py (snap-fixed protected points; the tool's 0.5/0.18/0.06 as the goose was built) -> the goose's own
# shrink_shadow_lods.py and carry_variants.py (variants goose_a/goose_b on the LODs; as ../mm9_goose_claude/scripts/build_runtime.sh) -> UV chart audit (hard gate),
# same_clips, winding. Materials (specular/metallic extras) are carried by the swap; clips are byte-identical, so the floor pass
# is not re-run. Usage: scripts/build_cand.sh <label_rNN>  -> export/cand_<label_rNN>/mm9_goose.glb
set -euo pipefail
cd "$(dirname "$0")/.."
t=$1; o=export/cand_$t; mkdir -p $o
export SOLE=${SOLE:-0.002} TIPS=${TIPS:-1} OUTLINE_BANDS=${OUTLINE_BANDS:-8} LIE=${LIE:-0.004} NODE=Goose TIP_BONES=${TIP_BONES:-Xtail,Xtoea,Xtoea01} EXT_BONES=${EXT_BONES:-Xfoot,Xfoot01} CORPSE=Death,Dead
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/swap_mp.py before/mm9_goose.glb work/mp_$t.npz $o/lod0.glb 2>&1 | grep -v RuntimeWarning
$BL -P scripts/build_lods.py -- $o/lod0.glb $o/lods.glb 2>&1 | grep -E "PROTECTED|CORPSE|LOD triangles|Error|Traceback"
$G scripts/shrink_shadow_lods.py $o/lods.glb $o/shadow.glb Goose 2>&1 | grep -v RuntimeWarning | tail -3
cp $o/shadow.glb $o/mm9_goose.glb
$G scripts/carry_variants.py $o/mm9_goose.glb 2>&1 | grep -v RuntimeWarning
$G ../claude_shared/reduction_uv_audit.py $o/mm9_goose.glb before/mm9_goose.glb --json review/uv_audit_$t.json 2>&1 | grep -v RuntimeWarning | tail -8
$G scripts/same_clips.py before/mm9_goose.glb $o/mm9_goose.glb 2>&1 | grep -v RuntimeWarning | tail -3
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $o/mm9_goose.glb 2>&1 | grep -v RuntimeWarning | tail -1
sha256sum $o/mm9_goose.glb
