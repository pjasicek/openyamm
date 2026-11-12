#!/usr/bin/env bash
# Mesh chain before the paint: clean -> fit -> rig (weights, skirt hinges, cloak chains) -> MPFB hands -> half-joint helpers.
# Usage (project folder): scripts/rebuild_mesh.sh   (never after the UV upload went to Meshy)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
export TOKEN=$(cat work/token) BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions
W=$here/work
scripts/B.sh clean_thf.py $here/../mm6_thf_claude/work/step1_v1.blend $here/../mm9_highwayman_claude/source/true/highwayman1_true.glb $W/clean_v1.blend $W/clean_v1.json | cut -c1-200
scripts/B.sh fit_thf.py $W/clean_v1.blend $here/scripts/fit_thf.json $W/fit_v1.blend $W/fit_v1.json | cut -c1-120
scripts/B.sh rig_thf.py $W/fit_v1.blend $W/rig_v1.blend $W/rig_v1.json | cut -c1-200
scripts/B.sh graft_hands.py $here/scripts/graft_thf.json | grep -E "^GRAFT|FAILED" | cut -c1-600
scripts/B.sh helpers_thf.py $W/hands_v1.blend $W/helpers_v1.blend
scripts/B.sh prune_hidden.py $W/helpers_v1.blend $W/pruned_v1.blend
