#!/usr/bin/env bash
# Rebuild the package h17 exports (MM8 Pirate Warrior m412, Crossbowman m416, Mage m420, Bedraggled Human m620,
# Human Mercenary m656) from their pre-gait sources and check them (winding, prefix).
#   scripts/rebuild.sh [model ...]   (models: m412 m416 m420 m620 m656; default all)
# Inputs: the installed GLBs as they were before this work (work/mm8_<m>_pre_gait.glb), the job files in jobs/ and the
# library loops in work/sources/ (copied from ../h06/work/sources/ and ../../mm8_pirates_gait_claude/work/sources/;
# library-derived data: never commit). The gates per descriptor group are listed in README.md (scripts/gate_only.py).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
declare -A CLIPS=([m412]="sprint" [m416]="sprint jog2" [m420]="walkslow walk3" [m620]="walk2" [m656]="sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m412 m416 m420 m620 m656)
for m in "${models[@]}"; do
    name="mm8_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(cat "review/${m}_winding.txt"); $(python3 scripts/prefix_check.py "work/${name}_pre_gait.glb" "export/$name.glb")"
done
