#!/usr/bin/env bash
# Rebuild the package h12 exports (MM7 Devil, Elf Archer, Elf Spearman, Goblin, Blaster Guy) from their pre-gait
# sources and run the gates.
#   scripts/rebuild.sh [model ...]   (models: m178 m214 m218 m246 m475; default all)
# Inputs: the installed GLBs as they were before this work (work/mm7_<m>_pre_gait.glb), the job files in jobs/, the
# library loops in work/sources/ (copied from ../h21/work/sources/; library-derived data: never commit) and, for the
# Blaster Guy's cape, work/m475_chains.json (scripts/dump_chains.py on ../../mm7_m475_claude/export/mm7_m475.blend).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
declare -A CLIPS=([m178]="Walk2 Jog" [m214]="Walk2 Jog" [m218]="Walk2 Jog Sprint" [m246]="Jog Sprint" [m475]="Jog")
declare -A SETS=([m178]="--set walking=Walk2 --set run=Jog"
                 [m214]="--set walking=Walk2 --set run=Jog"
                 [m218]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [m246]="--set run=Jog --set sprint=Sprint"
                 [m475]="--set run=Jog")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m178 m214 m218 m246 m475)
for m in "${models[@]}"; do
    name="mm7_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip,,}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    cp "export/$name.compose.json" "review/$name.compose.json"
    # shellcheck disable=SC2086
    (cd "$root" && python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world mm7 \
        --model "$name.glb" --candidate "$here/export/$name.glb" ${SETS[$m]}) > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
