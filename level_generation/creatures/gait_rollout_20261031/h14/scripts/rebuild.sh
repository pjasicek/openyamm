#!/usr/bin/env bash
# Rebuild the package h14 exports (MM7 human peasants m342, m352, m362, m372) from their pre-gait sources and run the
# gates (gait gate with the bindings, winding).
#   scripts/rebuild.sh [model ...]   (models: m342 m352 m362 m372; default all)
# Inputs: the installed GLBs as they were before this work (work/mm7_<m>_pre_gait.glb), the job files in jobs/, the
# library loops in work/sources/ (copied from ../h12/work/sources/; library-derived data: never commit) and, for the
# women's skirts, work/<m>_chains.json (scripts/dump_chains.py on ../../mm7_<m>_claude/work/rig_v6.blend).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
declare -A CLIPS=([m342]="Walk2 Jog" [m352]="Jog" [m362]="Jog" [m372]="Walk2 Jog")
declare -A SETS=([m342]="--set walking=Walk2 --set run=Jog"
                 [m352]="--set run=Jog"
                 [m362]="--set run=Jog"
                 [m372]="--set walking=Walk2 --set run=Jog")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m342 m352 m362 m372)
for m in "${models[@]}"; do
    name="mm7_$m"
    [[ -f "work/${m}_chains.json" ]] || [[ $m == m352 || $m == m362 ]] || \
        /snap/bin/blender --background --factory-startup --python scripts/dump_chains.py -- \
            "../../${name}_claude/work/rig_v6.blend" "work/${m}_chains.json" > /dev/null
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
