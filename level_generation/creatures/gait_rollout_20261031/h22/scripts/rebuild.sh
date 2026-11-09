#!/usr/bin/env bash
# Rebuild the package h22 exports (MM8 Crystal Walker m596, Plane Guardian m592) from their pre-gait sources and run the
# gates (gait_gate.py with the bindings of bindings.yml, check_winding.py).
#   scripts/rebuild.sh [m596] [m592]   (default both)
# Inputs: work/mm8_<m>_pre_gait.glb (the installed sources before this work, SHA-256 in work/pre_gait.sha256), the job
# files in jobs/, for m596 the walker's clip master ../../mm8_m596_v2_claude/work/anim_gait2.blend (read only) and its
# unchanged add_clips.py, for m592 the humanoid-set sprint in work/sources/ (copied from ../h13/work/sources/;
# library-derived data: never commit). Reproduces work/exports.sha256.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review work/sources
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m596 m592)
for m in "${models[@]}"; do
    case $m in
    m596)
        /snap/bin/blender -b -P scripts/walker_sprint.py -- ../../mm8_m596_v2_claude/work/anim_gait2.blend \
            work/walker_sprint.blend work/walker_sprint_donor.glb work/walker_sprint_report.json 2>&1 | grep CLIP
        rm -f work/walker_sprint.blend1
        python3 ../../mm8_m596_v2_claude/scripts/add_clips.py work/mm8_m596_pre_gait.glb work/walker_sprint_donor.glb \
            export/mm8_m596.glb --clips Sprint
        sets="--set sprint=Sprint";;
    m592)
        # the Guardian's own Walking and Running as library-style sources (legs for Walk2 and Jog)
        python3 scripts/glb_source.py work/mm8_m592_pre_gait.glb Running work/sources/m592_Running.npz 60
        python3 scripts/glb_source.py work/mm8_m592_pre_gait.glb Walking work/sources/m592_Walking.npz 60
        python3 scripts/compose_gait.py work/mm8_m592_pre_gait.glb export/mm8_m592.glb jobs/m592_walk2.json \
            jobs/m592_jog.json jobs/m592_sprint.json > work/m592_compose.log
        mv export/mm8_m592.compose.json review/mm8_m592.compose.json
        sets="--set walking=Walk2 --set run=Jog --set sprint=Sprint";;
    *) echo "unknown model $m"; exit 1;;
    esac
    # shellcheck disable=SC2086
    (cd "$root" && python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world mm8 \
        --model "mm8_$m.glb" --candidate "$here/export/mm8_$m.glb" $sets) > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/mm8_$m.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
