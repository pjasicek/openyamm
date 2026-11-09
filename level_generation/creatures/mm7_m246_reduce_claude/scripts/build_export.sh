#!/usr/bin/env bash
# Reduced Goblin runtime GLB from the picked ladder candidate (copied from mm7_m162_reduce_claude): export_cand.py ->
# swap_lod0.py (into the rollback source: materials, variants, region ramps and clips unchanged) -> build_lods.py ->
# shrink_shadow_lods.py -> carry_variants.py [-> keep_source_lods.py] -> export/mm7_m246.glb. The broadsword attachment is copied unchanged.
# Every step runs in a memory-capped scope (cap.sh). Usage: TOKEN=<lease> scripts/build_export.sh <blend> <Cand_NN>
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
blend=$1; cand=$2; out=export/mm7_m246.glb
cp work/$blend work/ladder.blend
REA_CAND=$cand REA_NODE=M246 PAT="FLOOR|EXPORTED" scripts/b.sh export_cand.py
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m246_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M246
REA_FLOOR_M=${REA_FLOOR_M:-0.004} PAT="PROTECTED|LOD tri" scripts/b.sh build_lods.py
scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
# m246: LOD3 from the source (the rebuilt LOD3 flattened the crest and hid the face; REA_KEEP_SOURCE_LODS=3)
if [ -n "${REA_KEEP_SOURCE_LODS:-}" ]; then scripts/cap.sh python3 scripts/keep_source_lods.py work/mm7_m246_source_pre_reduce.glb $out $REA_KEEP_SOURCE_LODS M246; fi
cp work/mm7_m246_sword_source_pre_reduce.glb export/mm7_m246_sword.glb
ls -la $out export/mm7_m246_sword.glb
