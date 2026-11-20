#!/usr/bin/env bash
# Rebuild the package h11 exports (MM7 Cleric Moon, Cleric Sun, Mage, Warlock, Necromancer) from their pre-gait
# sources and run the gates.
#   scripts/rebuild.sh [model ...]   (models: m274 m426 m294 m170 m174; default all)
# Inputs: the installed GLBs as they were before this work (work/mm7_<m>_pre_gait.glb), the job files in jobs/, the
# library loops in work/sources/ (copied from ../h09/work/sources/: library-derived, never commit) and the cloth chains
# work/<m>_chains.json (scripts/dump_chains.py on ../../mm7_<m>_claude/work/rig_v6.blend).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
declare -A CLIPS=([m274]="Jog" [m426]="Jog" [m294]="Jog" [m170]="Walk2 Jog" [m174]="Walk2 Jog")
declare -A SETS=([m274]="--set run=Jog" [m426]="--set run=Jog" [m294]="--set run=Jog"
                 [m170]="--set walking=Walk2 --set run=Jog --set stride_length=1.417 --set run_stride_length=2.143"
                 [m174]="--set walking=Walk2 --set run=Jog --set stride_length=1.319 --set run_stride_length=2.043")
# Cleric Sun A chases at a walking pace (Froude 0.60): its run stays Walking (walk-as-run); B/C jog. The shared gate
# applies --set to every descriptor, so tier A is gated separately (scripts/gate_only.py, a copy of ../q2's).
declare -A ONLY=([m174]="Cleric Sun B,Cleric Sun C")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m274 m426 m294 m170 m174)
for m in "${models[@]}"; do
    name="mm7_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip,,}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json" 2>/dev/null || true
    # shellcheck disable=SC2086
    if [[ -n ${ONLY[$m]:-} ]]; then
        # shellcheck disable=SC2086
        python3 scripts/gate_only.py --only "${ONLY[$m]}" --world mm7 --model "$name.glb" \
            --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
        python3 scripts/gate_only.py --only "Cleric Sun A" --world mm7 --model "$name.glb" \
            --candidate "export/$name.glb" --set walking=Walk2 --set stride_length=1.319 \
            > "review/${m}_gait_gate_tier_a.txt" || true
        echo "$m tier A: $(tail -1 "review/${m}_gait_gate_tier_a.txt")"
    else
        # shellcheck disable=SC2086
        python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm7 --model "$name.glb" \
            --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
    fi
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
