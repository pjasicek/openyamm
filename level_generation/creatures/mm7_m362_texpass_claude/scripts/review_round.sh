#!/usr/bin/env bash
# Builds export/mm7_m362_<tag>.glb from the installed backup and textures/m362_tp_*, bakes the viewer variants and
# shoots head close-ups (front, 3/4) of every skin. Usage (repository root): review_round.sh <tag>
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm7_m362_texpass_claude
TAG=$1
python3 $P/scripts/apply_layout.py $P/work/before_texpass/mm7_m362.glb $P/work/uv_final.npz $P/textures/m362_tp \
    $P/export/mm7_m362_$TAG.glb > /dev/null
python3 $P/scripts/viewer_variants.py $P/export/mm7_m362_$TAG.glb $TAG > /dev/null
python3 $P/scripts/viewer_manifest.py m362_ab_$TAG texpass-20261101-$TAG before=installed "$TAG=texture pass" > /dev/null
for t in aa ab ac ba bb bc ca cb cc; do
    python3 tools/run_creature_review.py --project $P --token "$(awk '{print $3}' $P/work/LEASE.txt)" \
        --tier m362_${t}_$TAG shots ${TAG}_${t}_hf:Standing:0:front:head ${TAG}_${t}_hq:Standing:0:quarter:head ${TAG}_${t}_sq:Standing:0:quarter:shoulders ${TAG}_${t}_sf:Standing:0:front:shoulders ${TAG}_${t}_ff:Standing:0:front:skirt ${TAG}_${t}_fr:Standing:0:right:skirt ${TAG}_${t}_fq:Standing:0:quarter:skirt \
        > /dev/null
done
echo "ROUND $TAG"
