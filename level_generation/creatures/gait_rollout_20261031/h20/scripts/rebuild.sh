#!/usr/bin/env bash
# Rebuild the package h20 exports (MM8 Troll m476, Troll Peasant m480, Minotaur m484, Minotaur Peasant m488) from their
# pre-gait sources and run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: m476 m480 m484 m488; default all)
# --sources: extract the library loops first (Blender, anim_library/ needed; library-derived data: never commit).
# Inputs: the installed GLBs as they were before this work (assets_source commit d4c87ca, kept in work/ as
# mm8_<m>_pre_gait.glb), the job files in jobs/ and the loops in work/sources/.
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
        "$lib/Armed/RPG-Character@Armed-Walk.FBX" "$lib/Armed/RPG-Character@Armed-Run-Forward.FBX" | grep EXTRACT
fi
declare -A JOBS=([m476]="m476_walk2 m476_jog m476_sprint" [m480]="m480_walk2"
                 [m484]="m484_walk2 m484_jog m484_sprint" [m488]="m488_jog m488_sprint")
declare -A SETS=([m476]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [m480]="--set walking=Walk2 --set run=Walking --set run_stride_length=1.494"
                 [m484]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [m488]="--set run=Jog --set sprint=Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m476 m480 m484 m488)
for m in "${models[@]}"; do
    name="mm8_$m"
    [[ -f "work/${name}_pre_gait.glb" ]] || git -C "$root/assets_source" show "d4c87ca:worlds/mm8/models/$name.glb" \
        > "work/${name}_pre_gait.glb"
    jobs=(); for j in ${JOBS[$m]}; do jobs+=("jobs/$j.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    # shellcheck disable=SC2086
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm8 --model "$name.glb" \
        --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
