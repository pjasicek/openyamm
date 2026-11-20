#!/usr/bin/env bash
# Rebuild the gait rollout h02 exports (MM6 BDwarf, BMinotaur, Jackalman, Werewolf) from their pre-gait sources and
# run the gates.   scripts/rebuild.sh [--sources] [m ...]   (m: dwa1 min1 jak1 wwf; default all)
# Inputs: work/mm6_<m>_pre_gait.glb (the installed sources before this work: assets_source/worlds/mm6/models/ as of
# 2026-10-31, SHA-256 in README.md), jobs/, and the library loops in work/sources/ (library-derived, never commit;
# --sources re-extracts them with Blender from anim_library/). The Werewolf's Mixamo-named rig is renamed to B_* names
# for the composer and back (scripts/rename_rig.py).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p work/sources export review
if [[ ${1:-} == --sources ]]; then
    shift
    hs="$root/anim_library/humanoid_set"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$hs/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" "$hs/Unarmed/RPG-Character@Unarmed-Sprint.FBX" \
        "$hs/Armed/RPG-Character@Armed-Walk.FBX" "$root/anim_library/mixamo/Mutant Walking.fbx" | grep EXTRACT
fi
models=("$@"); [[ ${#models[@]} -eq 0 ]] && models=(dwa1 min1 jak1 wwf)
for m in "${models[@]}"; do
    case $m in
        dwa1) jobs=(jobs/dwa1_walk2.json jobs/dwa1_run2.json jobs/dwa1_sprint.json); node=Axe; old=Walking,Running
              new=Walk2,Run2,Sprint; scale=101.66; set=(--set walking=Walk2 --set run=Run2 --set sprint=Sprint) ;;
        min1) jobs=(jobs/min1_run2.json jobs/min1_sprint.json); node=Axe; old=Walking,Running; new=Run2,Sprint
              scale=135; set=(--set run=Run2 --set sprint=Sprint) ;;
        jak1) jobs=(jobs/jak1_walk2.json jobs/jak1_run.json jobs/jak1_sprint.json); node=Staff; old=Walking
              new=Walk2,Run,Sprint; scale=109.23; set=(--set walking=Walk2 --set run=Run --set sprint=Sprint) ;;
        wwf)  jobs=(jobs/wwf_walk2.json jobs/wwf_run2.json jobs/wwf_sprint.json); node=-; old=Walking,Running
              new=Walk2,Run2,Sprint; scale=145.1; set=(--set walking=Walk2 --set run=Run2 --set sprint=Sprint) ;;
        *) echo "unknown model $m" >&2; exit 2 ;;
    esac
    if [[ $m == wwf ]]; then
        python3 scripts/rename_rig.py work/mm6_wwf_pre_gait.glb work/mm6_wwf_pre_gait_B.glb to_b > /dev/null
        python3 scripts/compose_gait.py work/mm6_wwf_pre_gait_B.glb work/mm6_wwf_export_B.glb "${jobs[@]}" \
            > work/wwf_compose.log
        mv work/mm6_wwf_export_B.compose.json review/mm6_wwf.compose.json
        python3 scripts/rename_rig.py work/mm6_wwf_export_B.glb export/mm6_wwf.glb from_b > /dev/null
    else
        python3 scripts/compose_gait.py "work/mm6_${m}_pre_gait.glb" "export/mm6_$m.glb" "${jobs[@]}" \
            > "work/${m}_compose.log"
        mv "export/mm6_$m.compose.json" "review/mm6_$m.compose.json"
    fi
    scripts/gates.sh "$m" "$node" "$old" "$new" "$scale" "${set[@]}"
done
