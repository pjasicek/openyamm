#!/usr/bin/env bash
# Reduced runtime GLB from the picked ladder step (Cand_83 of work/ladder_h.blend): export_cand -> swap_lod0 (onto the
# batch I export, work/mm7_m298_source_pre_reduce.glb) -> LODs (the tool's default ratios as the batch I build; protected
# extremes and Death/Dead floor contact) -> shadow LODs (the batch I project's own step) -> colour variants carried to
# every LOD/shadow primitive. Blender through tools/run_creature_blender.sh (lease token in CREATURE_3D_TOKEN).
# Usage: scripts/build_reduced.sh <out.glb>   (smooth shading, as the batch I export)
set -euo pipefail
cd "$(dirname "$0")/.."; P=$(pwd); REPO=$(cd ../../.. && pwd); R=${P#$REPO/}; out=${1:-export/mm7_m298.glb}
B() { local o; o=$(cd "$REPO" && tools/run_creature_blender.sh "$@" 2>&1) || { echo "$o"; exit 1; }; sed -n 's/^Blender log: //p' <<< "$o"; }
cp work/ladder_h.blend work/ladder.blend
grep EXPORTED "$(REA_CAND=Cand_83 REA_NODE=Ooze B $R/scripts/export_cand.py)"
python3 scripts/swap_lod0.py work/mm7_m298_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb Ooze
grep -E "PROTECTED|RATIOS|LOD triangles" "$(REA_LOD_RATIOS=${REA_LOD_RATIOS:-0.5,0.18,0.06} REA_FLOOR_M=${REA_FLOOR_M:-0.004} B $R/scripts/build_lods.py)"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb
cp work/pick_lods_shadowfix.glb "$out"; python3 scripts/carry_variants.py "$out"; ls -la "$out"
