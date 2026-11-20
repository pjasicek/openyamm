#!/usr/bin/env bash
# Rebuild the package h01 exports (MM6 BThief, Barbarian, FighterLeath, FighterChain) from their pre-gait sources and
# run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: thf bar1 fgt figc; default all)
# --sources: extract the library loops first (Blender, anim_library/ needed; library-derived data: never commit).
# Inputs: the installed GLBs as they were before this work (assets_source commit a762c96, kept in work/ as
# mm6_<m>_pre_gait.glb), the job files in jobs/, the loops in work/sources/ and, for the Thief's cloak, the chain rest
# points dumped from ../../mm6_thf_claude/work/rig_v3.blend (work/thf_cloak_chains.json, scripts/dump_cloak_chains.py).
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
        "$lib/humanoid_set/Unarmed/RPG-Character@Unarmed-Sprint.FBX" "$lib/mixamo/Walk.fbx" | grep EXTRACT
fi
if [[ ! -f work/thf_cloak_chains.json ]]; then
    /snap/bin/blender --background --factory-startup --python scripts/dump_cloak_chains.py -- \
        work/thf_cloak_chains.json "$root/level_generation/creatures/mm6_thf_claude/work/rig_v3.blend" | grep DUMPED
fi
declare -A JOBS=([thf]="thf_walk2 thf_jog thf_sprint" [bar1]="bar1_jog bar1_sprint" [fgt]="fgt_sprint"
                 [figc]="figc_jog figc_sprint")
declare -A SETS=([thf]="--set walking=Walk2 --set run=Jog --set sprint=Sprint" [bar1]="--set run=Jog --set sprint=Sprint"
                 [fgt]="--set sprint=Sprint" [figc]="--set run=Jog --set sprint=Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(thf bar1 fgt figc)
for m in "${models[@]}"; do
    name="mm6_$m"
    [[ -f "work/${name}_pre_gait.glb" ]] || git -C "$root/assets_source" show "a762c96:worlds/mm6/models/$name.glb" \
        > "work/${name}_pre_gait.glb"
    jobs=(); for j in ${JOBS[$m]}; do jobs+=("jobs/$j.json"); done
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    # shellcheck disable=SC2086
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm6 --model "$name.glb" \
        --candidate "export/$name.glb" ${SETS[$m]} > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
