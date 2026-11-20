#!/usr/bin/env bash
# Rebuild the package h21 exports (MM8 Ratman, Wererat human form, Vampire, Skeleton Archer, Dark Dwarf) from their
# pre-gait sources and run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: ratman m444 m468 m628 m632; default all)
# --sources: extract the library loops first (Blender, anim_library/ needed; library-derived data: never commit).
# Inputs: the installed GLBs as they were before this work (work/mm8_<m>_pre_gait.glb), the job files in jobs/ and the
# loops in work/sources/.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p work/sources export review
if [[ ${1:-} == --sources ]]; then
    shift
    lib="$root/anim_library/humanoid_set"
    mix="$root/anim_library/mixamo"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$lib/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" "$lib/Unarmed/RPG-Character@Unarmed-Sprint.FBX" \
        "$lib/2Hand Bow/RPG-Character@2Hand-Bow-Walk.FBX" "$lib/2Hand Bow/RPG-Character@2Hand-Bow-Walk-Slow.FBX" \
        "$lib/2Hand Crossbow/RPG-Character@2Hand-Crossbow-Walk.FBX" | grep EXTRACT
    echo "Walk.npz and Mutant_Walking.npz: Mixamo loops, copied from ../h19/work/sources/ (see README)"
fi
# new clips per model (job files jobs/<m>_<clip lower case>.json) and the gate's --set arguments
declare -A CLIPS=([ratman]="Sprint" [m444]="Walk2 Jog Sprint" [m468]="Walk2 Jog Sprint" [m628]="Walk2 WalkFast"
                  [m632]="Walk2 Sprint")
declare -A SETS=([ratman]="--set sprint=Sprint" [m444]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [m468]="--set walking=Walk2 --set run=Jog --set sprint=Sprint" [m628]="--set walking=Walk2 --set run=WalkFast"
                 [m632]="--set walking=Walk2 --set sprint=Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(ratman m444 m468 m628 m632)
for m in "${models[@]}"; do
    name="mm8_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip,,}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json" 2>/dev/null || true
    # shellcheck disable=SC2086
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm8 --model "$name.glb" \
        --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
