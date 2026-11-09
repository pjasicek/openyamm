#!/usr/bin/env bash
# Rebuild the package h16 exports (MM8 Lizardman Peasant, Dragon Hunter, Triton, Lizardman Warrior) from their pre-gait
# sources and run the gates.
#   scripts/rebuild.sh [--sources] [model ...]   (models: lizardman_peasant m456 m576 m404; default all)
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
        "$lib/Relax/RPG-Character@Relax-Run-Forward.FBX" | grep EXTRACT
fi
declare -A RUN=([lizardman_peasant]=Run [m456]=Jog [m576]=Jog [m404]=Jog)
declare -A JOB=([lizardman_peasant]=peasant [m456]=m456 [m576]=m576 [m404]=m404)
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(lizardman_peasant m456 m576 m404)
for m in "${models[@]}"; do
    name="mm8_$m"
    [[ -f "work/${name}_pre_gait.glb" ]] || git -C "$root/assets_source" show "d4c87ca:worlds/mm8/models/$name.glb" \
        > "work/${name}_pre_gait.glb"
    run="${RUN[$m]}"; job="${JOB[$m]}"
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "jobs/${job}_${run,,}.json" \
        "jobs/${job}_sprint.json" > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm8 --model "$name.glb" \
        --candidate "export/$name.glb" --set "run=$run" --set sprint=Sprint > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
