#!/usr/bin/env bash
# Package h04 copy of h02's gates.sh (Mixamo rigs renamed by rename_mixamo.py for the probes).
# Gates of one export of this package: gait_gate.py (with the binding changes), check_winding.py, the append-only
# identity check and the probes (phase, foot heading, bob, lowest skin, arm/prop contact, jerk/wrist, arm stretch,
# planted stride). Outputs in review/<m>_*.txt.
#   scripts/gates.sh <m> <prop node or -> <installed clips> <new clips> <scale> --set ... (gait_gate.py --set args)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
m=$1; node=$2; old=$3; new=$4; scale=$5; shift 5
glb="export/mm6_$m.glb"; probe="$glb"
if [[ $m == pfem || $m == pmn2 ]]; then
    python3 scripts/rename_mixamo.py "$glb" "work/mm6_${m}_B.glb" to_b > /dev/null
    probe="work/mm6_${m}_B.glb"
fi
python3 "$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py" --world mm6 --model "mm6_$m.glb" \
    --candidate "$glb" "$@" > "review/${m}_gait_gate.txt" || true
python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$glb" | tail -1 \
    > "review/${m}_winding.txt"
prop=()
for kind in staff; do
    attachment="$root/assets_source/worlds/mm6/models/mm6_${m}_$kind.glb"
    if [[ $node != - && -f $attachment ]]; then prop=("$node=$attachment"); fi
done
{
    python3 scripts/identity_check.py "work/mm6_${m}_pre_gait.glb" "$glb"
    echo "## phase (left foot forward-most, sole land/lift, stance share)"; python3 scripts/phase_probe.py "$probe" "$old,$new"
    echo "## foot heading (joint axis; toe-out from +Z)"; python3 scripts/foot_heading_probe.py "$probe" "$old,$new"
    echo "## head bob"; python3 scripts/bob_probe.py "$glb" "$old,$new"
    echo "## lowest skin"; python3 scripts/low_probe.py "$probe" "$new" "$scale"
    echo "## contact (forearm/hand/prop inside legs+trunk)"; python3 scripts/contact_probe.py "$probe" "$old,$new" "${prop[@]}"
    echo "## motion"; python3 scripts/motion_probe.py "$probe" "$old,$new"
    echo "## arm stretch"; python3 scripts/arm_stretch_probe.py "$probe" "$old,$new"
    echo "## planted stride per side"; python3 scripts/stride_probe.py "$probe" "$new"
    if [[ $m == pfem || $m == fmp ]]; then
        echo "## legs through the skirt"; python3 scripts/skirt_probe.py "$probe" "$old,$new"
    fi
} > "review/${m}_probes.txt" 2>&1
echo "$m: $(tail -1 "review/${m}_gait_gate.txt"); $(cat "review/${m}_winding.txt"); $(head -1 "review/${m}_probes.txt")"
