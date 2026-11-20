#!/usr/bin/env bash
# Reduced Angel runtime GLB from the picked ladder candidate (work/ladder.blend = ladder_h, Cand_79): export_cand.py ->
# swap_lod0.py (into the rollback source: materials, variants, region ramps and clips unchanged) -> build_lods.py ->
# shrink_shadow_lods.py -> carry_variants.py -> export/mm7_m150.glb. Every step memory-capped (cap.sh).
# Usage: scripts/build_export.sh [Cand_79]
set -euo pipefail
cd "$(dirname "$0")/.."
B="scripts/cap.sh /snap/bin/blender --background --factory-startup --python-exit-code 1"
out=export/mm7_m150.glb
REA_CAND=${1:-Cand_79} REA_NODE=M150 $B -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m150_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M150
REA_FLOOR_M=${REA_FLOOR_M:-0.0015} $B -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|RATIOS|LOD tri|Error"
scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
ls -la $out
