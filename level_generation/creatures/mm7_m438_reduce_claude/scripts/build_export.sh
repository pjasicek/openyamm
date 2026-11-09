#!/usr/bin/env bash
# Reduced Zombie runtime GLBs from the picked ladder candidate (copied from mm7_m262_reduce_claude): export_cand.py ->
# swap_lod0.py (into the rollback source: materials, variants, region ramps, clips, the Sword joint unchanged) ->
# build_lods.py (0.5 / 0.25 / 0.08, 8 influences as the m438 export, Death/Dead floor contacts and bounding extremes
# protected; REA_FLOOR_M=-1 by default: the 1 and 3 cm floor locks took LOD3 budget and collapsed the upper body into a wedge) -> the m438 project's shrink_shadow_lods.py (MESH_NODE=Zombie) -> carry_variants.py -> clamp_lod_uv.py.
# The forearm: work/forearm_r<NN>.glb from prop_reduce.py (LOD0 only; its LOD1-3 stay). Every step memory-capped.
# Usage: TOKEN=<lease> scripts/build_export.sh <ladder blend> <Cand_NN> <forearm step, e.g. r70>
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
blend=$1; cand=$2; prop=$3; out=export/mm7_m438.glb
cp work/$blend work/ladder.blend
REA_CAND=$cand REA_NODE=Zombie PAT="FLOOR|EXPORTED" scripts/b.sh export_cand.py
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m438_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb Zombie
REA_FLOOR_M=${REA_FLOOR_M:--1} PAT="PROTECTED|RATIOS|LOD tri" scripts/b.sh build_lods.py
MESH_NODE=Zombie scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
scripts/cap.sh python3 scripts/clamp_lod_uv.py $out
cp work/forearm_$prop.glb export/mm7_m438_forearm.glb
ls -la $out export/mm7_m438_forearm.glb
