#!/usr/bin/env bash
# Fish candidate runtime GLB from one mpqem step (goose copy): swap_mp.py (LOD0 index buffer only, every vertex an installed one) ->
# the fish's own runtime chain (../mm9_fish_claude/scripts/build_runtime.sh): set_extras.py --opaque-fins -> build_lods.py (the
# snap-fixed builder over both primitives; the tool's 0.5/0.18/0.06 as the fish was built) -> shrink_shadow_lods.py ->
# strip_shadow_fins.py -> set_extras.py (fins MASK 0.5) -> UV chart audit (hard gate), same_clips, winding. No tiers (no
# variants to carry). Clips are byte-identical (the swimmer lift is already in them), so floor_fix is not re-run.
# Usage: scripts/build_cand.sh <label_rNN>  -> export/cand_<label_rNN>/mm9_fish.glb
set -euo pipefail
cd "$(dirname "$0")/.."
t=$1; o=export/cand_$t; mkdir -p $o
export SOLE=${SOLE:-0.002} TOP=${TOP:-0.002} TIPS=${TIPS:-2} OUTLINE_BANDS=${OUTLINE_BANDS:-8} LIE=${LIE:-0.004} NODE=Fish \
  TIP_BONES=${TIP_BONES:-Xttop,Xtbot,Xtopfin,Xmidfin,Xmouth} EXT_BONES=${EXT_BONES:-Xsidefin,Xsidefin01,Xbotfin01,Xbotfin.001} CORPSE=Death,Dead
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/swap_mp.py before/mm9_fish.glb work/mp_$t.npz $o/lod0.glb 2>&1 | grep -v RuntimeWarning
$G scripts/set_extras.py $o/lod0.glb $o/lod0_opaque.glb --opaque-fins
$BL -P scripts/build_lods.py -- $o/lod0_opaque.glb $o/lods.glb 2>&1 | grep -E "PROTECTED|CORPSE|LOD triangles|Error|Traceback"
$G scripts/shrink_shadow_lods.py $o/lods.glb $o/shadow.glb Fish 2>&1 | grep -v RuntimeWarning | tail -3
$G scripts/strip_shadow_fins.py $o/shadow.glb $o/nofinshadow.glb Fish 2>&1 | grep -v RuntimeWarning | tail -1
$G scripts/set_extras.py $o/nofinshadow.glb $o/mm9_fish.glb
$G ../claude_shared/reduction_uv_audit.py $o/mm9_fish.glb before/mm9_fish.glb --json review/uv_audit_$t.json 2>&1 | grep -v RuntimeWarning | tail -8
$G scripts/same_clips.py before/mm9_fish.glb $o/mm9_fish.glb 2>&1 | grep -v RuntimeWarning | tail -3
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $o/mm9_fish.glb 2>&1 | grep -v RuntimeWarning | tail -1
sha256sum $o/mm9_fish.glb
