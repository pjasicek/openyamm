#!/usr/bin/env bash
# Viewer shots of the new clips of one model (tools/run_creature_review.py shots) and their sheets in review/.
#   scripts/shots.sh <m> <clip>:<length> [<clip>:<length> ...]
# Per clip: six phases from the left, the quarter and the front (feet focus).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
m=$1; shift
project="level_generation/creatures/mm7_${m}_gait_h08_claude"
specs=()
for item in "$@"; do
    clip=${item%%:*}; T=${item##*:}; lc=$(echo "$clip" | tr 'A-Z' 'a-z')
    for i in 0 1 2 3 4 5; do
        t=$(python3 -c "print(round($T*$i/6,4))")
        specs+=("${lc}_left_$i:$clip:$t:left:body" "${lc}_quarter_$i:$clip:$t:quarter:body" "${lc}_front_$i:$clip:$t:front:body" "${lc}_rear_$i:$clip:$t:rear:body")
    done
done
cd "$root"
python3 tools/run_creature_review.py --project "$project" shots "${specs[@]}" > /dev/null
python3 "$here/scripts/sheet_rows.py" "$root/$project/review/shots" "$here/review/${m}" "$@"
