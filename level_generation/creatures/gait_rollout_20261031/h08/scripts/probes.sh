#!/usr/bin/env bash
# All probes of one export into review/<m>_probes.txt: scripts/probes.sh <m> <old clips> <new clips> [skirt]
#   e.g. scripts/probes.sh m422 Walking Jog,Sprint skirt
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
m=$1; old=$2; new=$3; E=export/mm7_$m.glb
{
    echo "# probes of export/mm7_$m.glb (old clips: $old; new: $new)"
    echo "## bob (bob_audit measure)"; python3 scripts/bob_probe.py $E "$old,$new"
    echo "## foot heading (toe-out from +Z)"; python3 scripts/foot_heading_probe.py $E "$old,$new"
    echo "## phase"; python3 scripts/phase_probe.py $E "$old,$new"
    echo "## planted stride per side"; python3 scripts/stride_probe.py $E "$new"
    echo "## lowest skin point"; python3 scripts/low_probe.py $E "$new"
    echo "## jerk, wrist, pelvis"; python3 scripts/motion_probe.py $E "$old,$new"
    echo "## arm skin stretch"; python3 scripts/arm_stretch_probe.py $E "$old,$new"
    echo "## forearm/hand contacts (legs and trunk)"; python3 scripts/contact_probe.py $E "$old,$new" "${@:5}"
    if [[ ${4:-} == skirt ]]; then echo "## legs through the skirt"; python3 scripts/skirt_poke_probe.py $E "$old,$new"; fi
} 2>&1 | grep -v Warning > "review/${m}_probes.txt"
echo "review/${m}_probes.txt"
