#!/usr/bin/env bash
# Rebuild the package h13 exports (MM7 Peasant Dwarf Male m302, Dwarf Female m312, Elf Female m322, Elf Male m332)
# from their pre-gait sources and run the gates (gait_gate.py with the bindings of bindings.yml, check_winding.py).
#   scripts/rebuild.sh [model ...]   (models: m302 m312 m322 m332; default all)
# Inputs: the installed GLBs as they were before this work (work/mm7_<m>_pre_gait.glb, SHA-256 in
# work/pre_gait.sha256), the job files in jobs/, the library loops in work/sources/ (copied from ../h05, ../h04 and
# ../h12 work/sources/; library-derived data: never commit) and, for the Dwarf Female's dress, work/m312_chains.json
# (scripts/dump_chains.py on ../../mm7_m312_claude/work/rig_v6.blend). Reproduces work/exports.sha256.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
mkdir -p export review
declare -A SETS=([m302]="--set run=Jog" [m312]="--set run=Jog --set run_stride_length=2.395"
                 [m322]="--set run=Jog" [m332]="--set run=Jog")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(m302 m312 m322 m332)
for m in "${models[@]}"; do
    name="mm7_$m"
    python3 scripts/compose_gait.py "work/${name}_pre_gait.glb" "export/$name.glb" "jobs/${m}_jog.json" \
        > "work/${m}_compose.log"
    mv "export/$name.compose.json" "review/$name.compose.json"
    # shellcheck disable=SC2086
    (cd "$root" && python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world mm7 \
        --model "$name.glb" --candidate "$here/export/$name.glb" ${SETS[$m]}) > "review/${m}_gait_gate.txt" || true
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$name.glb" \
        | tail -1 > "review/${m}_winding.txt"
    echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt")"
done
