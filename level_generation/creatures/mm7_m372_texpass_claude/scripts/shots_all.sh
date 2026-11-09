#!/usr/bin/env bash
# Review-viewer shots of every skin, installed and texture pass, at the sheet cameras (repository root). The
# viewer's 'feet' focus is the face close-up in this project (review.js).
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm7_m372_texpass_claude
T=$(awk '{print $3}' "$P/work/LEASE.txt")
for k in ${SKINS:-aa ab ac ba bb bc}; do
    for v in ${VERSIONS:-before pass}; do
        python3 tools/run_creature_review.py --project "$P" --token "$T" --tier "m372_${k}_${v}" shots \
            "${k}_${v}_hf:Standing:0:front:head" "${k}_${v}_hq:Standing:0:quarter:head" \
            "${k}_${v}_ub:Standing:0:front:shoulders" "${k}_${v}_hands:Standing:0:front:skirt" \
            "${k}_${v}_bq:Standing:0:quarter:body" "${k}_${v}_back:Standing:0:back:body" \
            "${k}_${v}_cf:Standing:0:front:feet" "${k}_${v}_cq:Standing:0:quarter:feet" | tail -1
    done
done
