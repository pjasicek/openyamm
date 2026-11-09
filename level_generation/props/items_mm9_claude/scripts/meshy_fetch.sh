#!/usr/bin/env bash
# Poll each design's Smart Topology job until it settles, then download it.
# Usage (from the repository root): meshy_fetch.sh <token> <design> [...]
set -uo pipefail
here=level_generation/props/items_mm9_claude
project=$here/meshy
token=$1
shift
for design in "$@"; do
    version=$(python3 -I -c "import json,sys; print(json.load(open('$here/designs.json'))[sys.argv[1]].get('meshy_version','v1'))" "$design")
    job=${design}_st_${version}
    for _ in $(seq 60); do
        status=$(./tools/run_creature_meshy.sh --project "$project" --token "$token" poll --job "$job" \
            --wait-seconds 30 2>&1 | tail -1)
        case "$status" in
            *SUCCEEDED*) break ;;
            *FAILED*|*CANCELED*|*EXPIRED*) echo "$design FAILED $status"; continue 2 ;;
        esac
    done
    ./tools/run_creature_meshy.sh --project "$project" --token "$token" download --job "$job" 2>&1 | tail -1
    echo "$design FETCHED"
done
