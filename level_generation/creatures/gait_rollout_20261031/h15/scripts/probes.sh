#!/usr/bin/env bash
# All probes of one export into review/<m>_probes.txt.
#   scripts/probes.sh <m: mm7_7m452 ...> <export.glb> <installed clips> <new clips> [node=prop.glb ...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
m="$1"; glb="$2"; old="$3"; new="$4"; shift 4
s="$here/scripts"
{
    echo "## phase"; python3 "$s/phase_probe.py" "$glb" "$old,$new"
    echo "## foot heading"; python3 "$s/foot_heading_probe.py" "$glb" "$old,$new"
    echo "## bob"; python3 "$s/bob_probe.py" "$glb" "$old,$new"
    echo "## planted stride"; python3 "$s/stride_probe.py" "$glb" "$new"
    echo "## motion"; python3 "$s/motion_probe.py" "$glb" "$old,$new"
    echo "## arm stretch"; python3 "$s/arm_stretch_probe.py" "$glb" "$old,$new"
    echo "## contacts"; python3 "$s/contact_probe.py" "$glb" "$old,$new" "$@"
    echo "## lowest"; python3 "$s/low_probe.py" "$glb" "$new"
    echo "## prefix"; python3 "$s/prefix_check.py" "$here/work/${m}_pre_gait.glb" "$glb"
} > "$here/review/${m}_probes.txt" 2>&1
cat "$here/review/${m}_probes.txt"
