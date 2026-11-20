#!/usr/bin/env bash
# Rebuild the package h09 exports (MM7 Skeleton Warrior, Wight, Lich, Ghoul, Zombie) from their pre-gait sources and
# run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: m398 m430 m270 m470 m438; default all)
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
    mix="$root/anim_library/mixamo"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$lib/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" "$lib/Unarmed/RPG-Character@Unarmed-Sprint.FBX" \
        "$lib/2Hand Staff/RPG-Character@Staff-Run-Forward.FBX" "$mix/Walk.fbx" "$mix/Orc Walk.fbx" | grep EXTRACT
fi
# new clips per model (job files jobs/<m>_<clip lower case>.json) and the gate's --set arguments. The Wight has no foot
# geometry (floor-length robe): its strides are the foot-joint measurements, set explicitly (the gate cannot trust
# the hem's vertex measurement), and its installed Walking is rebound at its foot-joint stride too.
declare -A CLIPS=([m398]="Jog Sprint" [m430]="Jog Sprint" [m270]="Walk2 Jog" [m470]="Sprint" [m438]="Walk2 Jog Sprint")
declare -A SETS=([m398]="--set run=Jog --set sprint=Sprint"
                 [m430]="--set run=Jog --set sprint=Sprint --set stride_length=1.82 --set run_stride_length=2.399 --set sprint_stride_length=3.795"
                 [m270]="--set walking=Walk2 --set run=Jog" [m470]="--set sprint=Sprint"
                 [m438]="--set walking=Walk2 --set run=Jog --set sprint=Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m398 m430 m270 m470 m438)
for m in "${models[@]}"; do
    name="mm7_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip,,}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json" 2>/dev/null || true
    # shellcheck disable=SC2086
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm7 --model "$name.glb" \
        --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
