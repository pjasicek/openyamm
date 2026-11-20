#!/usr/bin/env bash
# Reduced Vampire runtime GLB from the picked ladder candidate (copied from mm7_m162_reduce_claude): export_cand.py ->
# swap_lod0.py (into the rollback source: materials, variants, region ramps and clips unchanged) -> build_lods.py ->
# shrink_shadow_lods.py -> carry_variants.py -> export/mm7_m422.glb.
# Every step runs in a memory-capped scope (cap.sh). Usage: TOKEN=<lease> scripts/build_export.sh <blend> <Cand_NN>
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
blend=$1; cand=$2; out=export/mm7_m422.glb
cp work/$blend work/ladder.blend
REA_CAND=$cand REA_NODE=M422 PAT="FLOOR|EXPORTED" scripts/b.sh export_cand.py
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m422_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M422
REA_FLOOR_M=${REA_FLOOR_M:-0.004} PAT="PROTECTED|LOD tri" scripts/b.sh build_lods.py
MESH=M422 scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
ls -la $out; sha256sum $out
