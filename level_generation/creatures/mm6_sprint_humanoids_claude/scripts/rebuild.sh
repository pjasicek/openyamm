#!/usr/bin/env bash
# Rebuild the Jog and Sprint exports of the MM6 Ogre and KnightPlate from their pre-sprint sources and run the gates.
#   scripts/rebuild.sh [--sources]   (--sources: extract the library loops first; Blender, anim_library/ needed)
# Inputs: the installed GLBs as they were before this work (assets_source commit d4c87ca), the job files in jobs/ and
# the library loops in work/sources/ (git-ignored library data: never commit).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
cd "$here"
mkdir -p work/sources export review
if [[ ${1:-} == --sources ]]; then
    /snap/bin/blender --background --factory-startup --python scripts/extract_source.py -- work/sources \
        "$root/anim_library/humanoid_set/Unarmed/RPG-Character@Unarmed-Run-Forward.FBX" \
        "$root/anim_library/humanoid_set/Unarmed/RPG-Character@Unarmed-Sprint.FBX" | grep EXTRACT
fi
for m in ogr kni; do
    [[ -f "work/mm6_${m}_pre_sprint.glb" ]] || git -C "$root/assets_source" show "d4c87ca:worlds/mm6/models/mm6_$m.glb" \
        > "work/mm6_${m}_pre_sprint.glb"
    python3 scripts/compose_gait.py "work/mm6_${m}_pre_sprint.glb" "export/mm6_$m.glb" "jobs/${m}_jog.json" \
        "jobs/${m}_sprint.json" > "work/${m}_final.log"
    mv "export/mm6_$m.compose.json" "review/mm6_$m.compose.json"
    python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm6 --model "mm6_$m.glb" \
        --candidate "export/mm6_$m.glb" --set run=Jog --set sprint=Sprint > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/mm6_$m.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
