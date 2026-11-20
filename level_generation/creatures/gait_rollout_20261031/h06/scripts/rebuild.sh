#!/usr/bin/env bash
# Rebuild the package h06 exports (MM6 Demon, Guard, BGoblin, Skeleton, LizardArch, ElemEarth) from their pre-gait
# sources and run the gates.
#   scripts/rebuild.sh [model ...]   (models: demon gua gob2 ske lzd ert; default all)
# Inputs: the installed GLBs as they were before this work (work/mm6_<m>_pre_gait.glb), the job files in jobs/ and the
# library loops in work/sources/ (copied from ../h21/work/sources/; library-derived data: never commit).
# The Mixamo-named rigs (demon, ske) are composed on a B_* renamed copy (scripts/rename_mixamo.py) and renamed back.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
declare -A CLIPS=([demon]="Walk2 Jog Sprint" [gua]="Jog Sprint" [gob2]="Sprint" [ske]="Walk2 Jog Sprint" [lzd]="Walk2 Jog"
                  [ert]="Walk2 Run Sprint")
declare -A SETS=([demon]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [gua]="--set run=Jog --set sprint=Sprint"
                 [gob2]="--set sprint=Sprint"
                 [ske]="--set walking=Walk2 --set run=Jog --set sprint=Sprint"
                 [lzd]="--set walking=Walk2 --set run=Jog"
                 [ert]="--set walking=Walk2 --set run=Run --set sprint=Sprint")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(demon gua gob2 ske lzd ert)
for m in "${models[@]}"; do
    name="mm6_$m"
    jobs=()
    for clip in ${CLIPS[$m]}; do jobs+=("jobs/${m}_${clip,,}.json"); done
    if [[ $m == demon || $m == ske ]]; then
        python3 scripts/rename_mixamo.py "work/${name}_pre_gait.glb" "work/${name}_b.glb" to_b > /dev/null
        python3 scripts/compose_gait.py "work/${name}_b.glb" "export/${name}_b.glb" "${jobs[@]}" > "work/${m}_compose.log"
        python3 scripts/rename_mixamo.py "export/${name}_b.glb" "export/$name.glb" from_b > /dev/null
        mv "export/${name}_b.compose.json" "review/$name.compose.json"
    else
        python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "${jobs[@]}" > "work/${m}_compose.log"
        mv "export/$name.compose.json" "review/$name.compose.json"
    fi
    # shellcheck disable=SC2086
    (cd "$root" && python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world mm6 \
        --model "$name.glb" --candidate "$here/export/$name.glb" ${SETS[$m]}) > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
