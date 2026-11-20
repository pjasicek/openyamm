#!/usr/bin/env bash
# Ladder candidate -> tier-A viewer GLB (rollback source's materials/clips, LOD0 only, bow and arrow attached) for
# glb_close.py. Usage: TOKEN=<lease> cand_glb.sh <ladder label> <Cand_NN> [bow glb] [arrow glb] -> work/glb_<label>_<NN>.glb, review/glbclose input work/view_<label>_<NN>.glb
set -euo pipefail
cd "$(dirname "$0")/.."; label=$1; cand=$2; bow=${3:-work/mm7_m154_bow_source_pre_reduce.glb}; arrow=${4:-work/mm7_m154_arrow_source_pre_reduce.glb}
cp work/ladder_$label.blend work/ladder.blend
REA_CAND=$cand REA_NODE=M154 scripts/bl.sh export_cand.py | grep EXPORTED
python3 scripts/swap_lod0.py work/mm7_m154_source_pre_reduce.glb work/cand_export.glb work/glb_${label}_${cand#Cand_}.glb M154 | tail -1
python3 scripts/viewer_variants.py work/glb_${label}_${cand#Cand_}.glb tmp_${label}_${cand#Cand_} > /dev/null
for t in b c; do rm -f review/viewer/mm7_m154_${t}_tmp_${label}_${cand#Cand_}.glb; done
mv review/viewer/mm7_m154_a_tmp_${label}_${cand#Cand_}.glb work/view_${label}_${cand#Cand_}.glb
python3 scripts/viewer_attach.py work/view_${label}_${cand#Cand_}.glb a Bow=$bow Arrow=$arrow | tail -1
