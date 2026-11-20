#!/usr/bin/env bash
# Reduced Necromancer runtime GLB from the picked ladder candidate (copied from mm7_m262_reduce_claude): export_cand.py ->
# swap_lod0.py (into the rollback source: materials, variants, region ramps, specular extras and clips unchanged) ->
# build_lods.py -> shrink_shadow_lods.py (the source chain's) -> carry_variants.py -> export/mm7_m294.glb.
# No attachment (the Necromancer holds nothing). Every step runs in a memory-capped scope (cap.sh).
# Usage: TOKEN=<lease> scripts/build_export.sh <blend> <Cand_NN>
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
blend=$1; cand=$2; out=export/mm7_m294.glb
cp work/$blend work/ladder.blend
REA_CAND=$cand REA_NODE=M294 PAT="FLOOR|EXPORTED" scripts/b.sh export_cand.py
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m294_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M294
REA_FLOOR_M=${REA_FLOOR_M:-0.004} PAT="PROTECTED|RATIOS|LOD tri" scripts/b.sh build_lods.py
MESH=M294 scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
rm -f work/pick_lods.geometry.glb
ls -la $out
