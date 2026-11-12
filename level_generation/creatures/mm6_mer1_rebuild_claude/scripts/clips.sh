#!/usr/bin/env bash
# Clips on the textured export: NOBLEMAN body roles + FIGHTERBASE Hattack2 (clips_mm9.py) -> right fist and wrist turn in the attack -> club from
# the belt into the fist (club_keys.py)
# -> half-joint helpers -> toes out of the floor in the runs -> robe chains (robe_keys.py) -> club into the fist in the attack (club_keys.py, after the robe: the club rides on Robe_03_0).
# Usage (project folder): scripts/clips.sh <body glb> <out glb>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G="$here/../claude_shared/gltf_venv/bin/python"
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning\|Warn" ; }
Q "$G" scripts/clips_mm9.py "$1" work/c1.glb scripts/roles_mer.json work/clips.json | tail -1 | cut -c1-250
Q "$G" scripts/finger_keys_mer.py work/c1.glb work/c2.glb work/hand_poses.json | tail -1
Q "$G" scripts/half_keys.py work/c2.glb work/c3.glb | tail -1
Q "$G" scripts/foot_clear.py work/c3.glb work/c4.glb Running Jog | tail -6 | tr "\n" " "; echo
Q "$G" scripts/robe_keys.py work/c4.glb work/c5.glb work/rig_v1.blend.robe.json work/robe_report.json | cut -c1-120 | tr "\n" " "; echo
Q "$G" scripts/club_keys.py work/c5.glb "$2" | tail -1
