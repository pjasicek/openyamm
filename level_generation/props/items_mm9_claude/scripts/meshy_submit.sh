#!/usr/bin/env bash
# Submit the Smart Topology job (5 credits) of each design whose master exists and that has no job yet.
# Usage (from the repository root): meshy_submit.sh <token> <design> [...]
set -uo pipefail
here=level_generation/props/items_mm9_claude
token=$1
shift
for design in "$@"; do
    [ -f "$here/meshy/$design/references_hd/00_three_quarter.png" ] || { echo "$design: no master yet"; continue; }
    version=$(python3 -I -c "import json,sys; print(json.load(open('$here/designs.json'))[sys.argv[1]].get('meshy_version','v1'))" "$design")
    grep -q "\"${design}_st_${version}\"" "$here/meshy/creature_3d_progress.json" && { echo "$design: submitted"; continue; }
    python3 -I "$here/scripts/mm9item.py" st-request "$design" >/dev/null
    ./tools/run_creature_meshy.sh --project "$here/meshy" --token "$token" submit --job "${design}_st_${version}" \
        --kind image-to-3d --request "requests/${design}_st_${version}.json" --credits 5 2>&1 | tail -1
done
