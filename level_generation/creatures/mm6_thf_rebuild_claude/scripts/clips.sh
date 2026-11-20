#!/usr/bin/env bash
# Clips on the textured export: MM9 HIGHWAYMAN/FIGHTERBASE roles -> hands and daggers -> half-joint helpers -> jerkin skirt hinges -> toes out of the floor
# (our boots are longer than MM9's feet) -> cloak chains.
# Usage (project folder): scripts/clips.sh <body glb> <out glb>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G="$here/../claude_shared/gltf_venv/bin/python"
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/clips_mm9.py "$1" work/c1.glb scripts/roles_thf.json work/clips.json | tail -1 | cut -c1-250
Q "$G" scripts/finger_keys_thf.py work/c1.glb work/c2.glb work/hand_poses.json | tail -1
Q "$G" scripts/half_keys.py work/c2.glb work/c3.glb | tail -1
Q "$G" scripts/skirt_keys.py work/c3.glb work/c4.glb work/skirt_report.json | tail -1
Q "$G" scripts/foot_clear.py work/c4.glb work/c5.glb Running Jog | tail -6 | tr "\n" " "; echo
Q "$G" scripts/cloak_keys.py work/c5.glb "$2" work/rig_v1.blend.cloak.json work/cloak_report.json | grep -v "^lift\|^CAPS" | cut -c1-90 | tr "\n" " "; echo
