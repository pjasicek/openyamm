#!/usr/bin/env bash
# Rebuild the package h19 exports (MM8 Ogre Warrior m440, Cyclops m520, Ogre Mage m540, Ogre Peasant m436) from their
# pre-gait sources and run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: m440 m520 m540 m436; default all)
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
    lib="$root/anim_library"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$lib/humanoid_set/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" \
        "$lib/humanoid_set/Unarmed/RPG-Character@Unarmed-Sprint.FBX" \
        "$lib/humanoid_set/Armed/RPG-Character@Armed-Walk.FBX" "$lib/mixamo/Orc Walk (1).fbx" | grep EXTRACT
fi
declare -A JOBS=([m440]="m440_jog m440_sprint" [m520]="m520_jog m520_sprint" [m540]="m540_walk2 m540_jog m540_sprint"
                 [m436]="m436_walk2")
declare -A SETS=([m440]="--set run=Jog --set sprint=Sprint" [m520]="--set run=Jog --set sprint=Sprint"
                 [m540]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [m436]="--set walking=Walk2 --set run=Walking --set run_stride_length=1.695")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m440 m520 m540 m436)
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
