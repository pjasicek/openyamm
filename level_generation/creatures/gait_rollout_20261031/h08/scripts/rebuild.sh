#!/usr/bin/env bash
# Rebuild package h08's exports (MM7 Thief m410, Troglodyte m418, Vampire m422, Monk m290) from their pre-gait
# sources and run the gates. Usage: scripts/rebuild.sh [m410 m418 m422 m290]   (default: all four)
# Inputs: work/mm7_<m>_pre_gait.glb (the installed sources before this work, also the rollback copies), the jobs in
# jobs/, the library loops in work/sources/ (copied from ../../mm6_sprint_humanoids_claude/work/sources and
# ../../mm8_pirates_gait_claude/work/sources; library-derived, never commit) and, for the robed bodies, the cloth
# chain definitions work/<m>_chains.json (scripts/dump_chains.py on ../../mm7_<m>_claude/work/rig_v6.blend).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
gate="$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py"
winding="$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py"
declare -A JOBS=([m410]="jog sprint" [m418]="lope jog sprint" [m422]="jog sprint" [m290]="jog sprint")
declare -A SETS=([m410]="--set run=Jog --set sprint=Sprint" [m418]="--set walking=Lope --set run=Jog --set sprint=Sprint"
                 [m422]="--set run=Jog --set sprint=Sprint" [m290]="--set run=Jog --set sprint=Sprint")
declare -A CHAINS=([m422]=m422 [m290]=m290)
models=("$@")
[[ ${#models[@]} -gt 0 ]] || models=(m410 m418 m422 m290)
for m in "${models[@]}"; do
    if [[ -n ${CHAINS[$m]:-} && ! -f work/${m}_chains.json ]]; then
        /snap/bin/blender --background --factory-startup --python scripts/dump_chains.py -- \
            "../../mm7_${m}_claude/work/rig_v6.blend" "work/${m}_chains.json" | grep CHAINS
    fi
    jobs=()
    for j in ${JOBS[$m]}; do jobs+=("jobs/${m}_$j.json"); done
    python3 scripts/compose_gait.py "work/mm7_${m}_pre_gait.glb" "export/mm7_$m.glb" "${jobs[@]}" > "work/$m.log"
    mv "export/mm7_$m.compose.json" "review/mm7_$m.compose.json"
    python3 "$root/level_generation/creatures/claude_shared/graft_byte_check.py" "work/mm7_${m}_pre_gait.glb" \
        "export/mm7_$m.glb" > "review/${m}_byte_check.txt"
    # shellcheck disable=SC2086
    python3 "$gate" --world mm7 --model "mm7_$m.glb" --candidate "export/mm7_$m.glb" ${SETS[$m]} \
        > "review/${m}_gait_gate.txt" || true
    python3 "$winding" "export/mm7_$m.glb" | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt"); $(tail -1 "review/${m}_byte_check.txt")"
done
