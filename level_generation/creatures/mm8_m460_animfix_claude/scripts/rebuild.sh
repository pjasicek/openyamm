#!/usr/bin/env bash
# Rebuild the package h18 exports (MM8 Dark Elf peasants m424/m428, Dark Elf Warrior m432, Ether Knight m604, Cleric
# m460) from their pre-gait sources, then run the gates (gait_gate.py with the bindings.yml values, winding, prefix).
#   scripts/rebuild.sh [--sources] [model ...]   (models: m424 m428 m432 m604 m460; default all)
# --sources: extract the two 2Hand-Sword walks with Blender (anim_library/ needed) and dump the dress/robe chain rest
# points from the projects' rig blends. The other library loops in work/sources/ are copies of ../h17/work/sources/
# (library-derived data: never commit).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
cd "$here"
mkdir -p work/sources export review
if [[ ${1:-} == --sources ]]; then
    shift
    lib="$root/anim_library/humanoid_set"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$lib/2Hand Sword/RPG-Character@2Hand-Sword-Walk.FBX" "$lib/2Hand Sword/RPG-Character@2Hand-Sword-Walk-Slow.FBX" \
        | grep EXTRACT
    c="$root/level_generation/creatures"
    /snap/bin/blender --background --factory-startup --python scripts/dump_cloak_chains.py -- \
        work/m428_dress_chains.json "$c/mm8_m428_claude/work/rig_sim.blend" cloak_chains Rig | grep DUMPED
    /snap/bin/blender --background --factory-startup --python scripts/dump_cloak_chains.py -- \
        work/m460_robe_chains.json "$c/mm8_m460_claude/work/motion_final.blend" cloak_chains Rig | grep DUMPED
fi
declare -A CLIPS=([m424]="walk2" [m428]="walk2" [m432]="walk2 jog" [m604]="walk2 jog sprint" [m460]="jog")
declare -A SETS=([m424]="--set walking=Walk2" [m428]="--set walking=Walk2"
                 [m432]="--set walking=Walk2 --set run=Jog --set sprint=Running --set sprint_stride_length=3.509"
                 [m604]="--set walking=Walk2 --set run=Jog --set sprint=Sprint" [m460]="--set run=Jog")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m424 m428 m432 m604 m460)
for m in "${models[@]}"; do
    name="mm8_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip}.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    # shellcheck disable=SC2086
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm8 --model "$name.glb" \
        --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt");" \
        "$(python3 scripts/prefix_check.py "work/${name}_pre_gait.glb" "export/$name.glb")"
done
