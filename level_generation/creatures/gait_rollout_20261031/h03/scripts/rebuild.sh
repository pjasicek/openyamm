#!/usr/bin/env bash
# Rebuild the package h03 exports (MM6 BArcher, BLich, Cleric, Druidess, Sorcerer) from their pre-gait sources and run
# the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: arc1 lch cle dru1 sor1; default all)
# --sources: extract the library loops first (Blender, anim_library/ needed; library-derived data: never commit) and the
# cloak chain rest points from the projects' rig blends (Cleric, Druidess) and the Sorcerer's GLB.
# Inputs: the installed GLBs as they were before this work (work/mm6_<m>_pre_gait.glb), jobs/, work/sources/ and the
# chain files work/{cle,dru1}_cloak_chains.json, work/sor1_robe_chains.json.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p work/sources export review
if [[ ${1:-} == --sources ]]; then
    shift
    lib="$root/anim_library/humanoid_set"
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$lib/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" \
        "$lib/2Hand Bow/RPG-Character@2Hand-Bow-Run-Forward.FBX" | grep EXTRACT
    c="$root/level_generation/creatures"
    /snap/bin/blender --background --factory-startup --python scripts/dump_cloak_chains.py -- \
        work/cle_cloak_chains.json "$c/mm6_cle_claude/work/rig_v4.blend" cle_cloak Cleric_Rig | grep DUMPED
    /snap/bin/blender --background --factory-startup --python scripts/dump_cloak_chains.py -- \
        work/dru1_cloak_chains.json "$c/mm6_dru1_claude/work/rig_v6.blend" cloak_chains Rig | grep DUMPED
    python3 scripts/chains_check.py work/mm6_sor1_pre_gait.glb work/sor1_robe_chains.json --from-glb Robe_
fi
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(arc1 lch cle dru1 sor1)
for m in "${models[@]}"; do
    name="mm6_$m"
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "jobs/${m}_jog.json" \
        > "work/${m}_compose.log"
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm6 --model "$name.glb" \
        --candidate "export/$name.glb" --set run=Jog > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
