#!/usr/bin/env bash
# Rebuild the package h10 exports (MM7 Behemoth, Dwarf, Golem, Troll, Minotaur) from their pre-gait sources and run
# the gates.   scripts/rebuild.sh [model ...]   (models: m162 m190 m254 m461 m286; default all)
# Inputs: the installed GLBs as they were before this work (work/mm7_<m>_pre_gait.glb), the job files in jobs/ and the
# library loops in work/sources/ (copied from ../h21/work/sources/; library-derived data: never commit).
# The Troll's bindings differ per tier (A/B keep Walking as their run), so it is gated twice with ../q2's gate_only.py.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
gate="level_generation/creatures/claude_shared/postprocess/gait_gate.py"
only="level_generation/creatures/gait_rollout_20261031/q2/scripts/gate_only.py"
declare -A CLIPS=([m162]="sprint" [m190]="walk2 sprint" [m254]="walk2 sprint" [m461]="walk2 run" [m286]="sprint")
declare -A SETS=([m162]="--set sprint=Sprint" [m190]="--set walking=Walk2 --set sprint=Sprint"
                 [m254]="--set walking=Walk2 --set sprint=Sprint"
                 [m286]="--set run=Running --set run_stride_length=2.117 --set sprint=Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m162 m190 m254 m461 m286)
for m in "${models[@]}"; do
    name="mm7_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    cand="$here/export/$name.glb"
    if [[ $m == m461 ]]; then
        (cd "$root" && python3 "$only" --only "ATroll A,ATroll B" --world mm7 --model "$name.glb" --candidate "$cand" \
            --set walking=Walk2 --set sprint=Run --set run_stride_length=1.494) > "review/${m}_gait_gate_ab.txt" || true
        (cd "$root" && python3 "$only" --only "ATroll C" --world mm7 --model "$name.glb" --candidate "$cand" \
            --set walking=Walk2 --set run=Run --set sprint=Run) > "review/${m}_gait_gate_c.txt" || true
        result="A/B $(tail -1 "review/${m}_gait_gate_ab.txt"), C $(tail -1 "review/${m}_gait_gate_c.txt")"
    else
        # shellcheck disable=SC2086
        (cd "$root" && python3 "$gate" --world mm7 --model "$name.glb" --candidate "$cand" ${SETS[$m]}) \
            > "review/${m}_gait_gate.txt" || true
        result="$(tail -1 "review/${m}_gait_gate.txt")"
    fi
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $result; $(cat "review/${m}_winding.txt")"
done
