#!/usr/bin/env bash
# Rebuild the package h07 exports (MM7 Chain, Leather and Plate Fighters, Swordsman) from their pre-gait sources and
# run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: m222 m226 m230 m406; default all)
# --sources: extract the library loops first (Blender, anim_library/ needed; library-derived data: never commit).
# Inputs: the installed GLBs as they were before this work (work/mm7_<m>_pre_gait.glb), the job files in jobs/ and the
# loops in work/sources/.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p work/sources export review
if [[ ${1:-} == --sources ]]; then
    shift
    lib="$root/anim_library/humanoid_set"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$lib/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" "$lib/Unarmed/RPG-Character@Unarmed-Sprint.FBX" \
        "$lib/Armed/RPG-Character@Armed-Walk.FBX" | grep EXTRACT
fi
# new clips per model (job files jobs/<m>_<clip lower case>.json) and the gate's --set arguments
declare -A CLIPS=([m222]="Walk2 Jog Sprint" [m226]="Jog Sprint" [m230]="Walk2 Jog Sprint" [m406]="Jog Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m222 m226 m230 m406)
for m in "${models[@]}"; do
    name="mm7_$m"
    jobs=(); sets=(--set run=Jog --set sprint=Sprint)
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip,,}.json"); done
    [[ " ${CLIPS[$m]} " == *" Walk2 "* ]] && sets+=(--set walking=Walk2)
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm7 --model "$name.glb" \
        --candidate "export/$name.glb" "${sets[@]}" > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
