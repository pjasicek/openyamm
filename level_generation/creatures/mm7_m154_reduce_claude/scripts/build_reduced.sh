#!/usr/bin/env bash
# Reduced Archer runtime GLBs from the picked ladder candidate (structure of ../mm7_m154_claude/scripts/build_runtime.sh
# after its attachment split and head merge): export_cand.py -> swap_lod0.py (into the rollback source: merged
# body+head material, tier variants, region ramps, clips, sockets unchanged) -> build_lods.py -> shrink_shadow_lods.py
# -> carry_variants.py -> export/mm7_m154.glb; bow and arrow LODs by ring removal (bow_rings.py, arrow_rings.py,
# prop_swap_lods.py) -> export/mm7_m154_bow.glb, export/mm7_m154_arrow.glb. Nothing is installed.
# Usage: TOKEN=<lease> scripts/build_reduced.sh [ladder label, default f] [Cand_NN, default Cand_81]
set -euo pipefail
cd "$(dirname "$0")/.."; label=${1:-f}; cand=${2:-Cand_81}; ROOT="$(cd ../../.. && pwd)"
cp work/ladder_$label.blend work/ladder.blend
REA_CAND=$cand REA_NODE=M154 scripts/bl.sh export_cand.py | grep -E "EXPORTED|Error"
python3 scripts/swap_lod0.py work/mm7_m154_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M154
scripts/bl.sh build_lods.py | grep -E "HORN|STRING|PROTECTED|RATIOS|LOD tri|Error"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb | tail -2
cp work/pick_lods_shadowfix.glb export/mm7_m154.glb
python3 scripts/carry_variants.py export/mm7_m154.glb
python3 scripts/arrow_rings.py
REA_BOW_TOL=0.003,0.012,0.02,0.05 python3 scripts/bow_rings.py work/grip_src.json 30,17,10,6
python3 scripts/prop_swap_lods.py work/mm7_m154_bow_source_pre_reduce.glb export/mm7_m154_bow.glb work/bow_lod{0,1,2,3}.npz
python3 scripts/prop_swap_lods.py work/mm7_m154_arrow_source_pre_reduce.glb export/mm7_m154_arrow.glb work/arrow_lod0.npz work/arrow_lod1.npz - -
python3 "$ROOT/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm7_m154.glb export/mm7_m154_bow.glb export/mm7_m154_arrow.glb > work/winding.log; grep -iE "inverted" work/winding.log | tail -3
ls -la export/
