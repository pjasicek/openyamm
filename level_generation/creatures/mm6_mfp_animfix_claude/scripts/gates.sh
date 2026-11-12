#!/usr/bin/env bash
# Package h05 copy of h04's gates.sh. Gates of one export of this package: gait_gate.py (with the binding changes),
# check_winding.py, the append-only identity check and the probes (phase, foot heading, bob, lowest skin, arm/prop
# contact, motion, arm stretch, planted stride). Outputs in review/<m>_*.txt.
#   scripts/gates.sh <m> <installed clips> <new clips> <scale> <props: node=file,... or -> --set ... (gait_gate.py --set)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
cd "$here"
m=$1; old=$2; new=$3; scale=$4; proplist=$5; shift 5
glb="export/mm6_$m.glb"
python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm6 --model "mm6_$m.glb" \
    --candidate "$glb" "$@" > "review/${m}_gait_gate.txt" || true
python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$glb" | tail -1 \
    > "review/${m}_winding.txt"
prop=()
if [[ $proplist != - ]]; then
    IFS=, read -ra pairs <<< "$proplist"
    for p in "${pairs[@]}"; do prop+=("${p%%=*}=$root/assets_source/worlds/mm6/models/${p#*=}"); done
fi
{
    python3 scripts/identity_check.py "work/mm6_${m}_pre_gait.glb" "$glb"
    echo "## phase (left foot forward-most, sole land/lift, stance share)"; python3 scripts/phase_probe.py "$glb" "$old,$new"
    echo "## foot heading (joint axis; toe-out from +Z)"; python3 scripts/foot_heading_probe.py "$glb" "$old,$new"
    echo "## head bob"; python3 scripts/bob_probe.py "$glb" "$old,$new"
    echo "## lowest skin"; python3 scripts/low_probe.py "$glb" "$new" "$scale"
    echo "## contact (forearm/hand/prop inside legs+trunk)"; python3 scripts/contact_probe.py "$glb" "$old,$new" "${prop[@]}"
    echo "## motion"; python3 scripts/motion_probe.py "$glb" "$old,$new"
    echo "## arm stretch"; python3 scripts/arm_stretch_probe.py "$glb" "$old,$new"
    echo "## planted stride per side"; python3 scripts/stride_probe.py "$glb" "$new"
} 2>&1 | grep -v -i warn > "review/${m}_probes.txt"
echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt"); $(head -1 "review/${m}_probes.txt")"
