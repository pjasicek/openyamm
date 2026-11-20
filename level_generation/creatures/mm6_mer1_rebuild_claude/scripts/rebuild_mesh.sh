#!/usr/bin/env bash
# Mesh chain before the paint: clean -> fit (centre rest frames = NOBLEMAN stand) -> rig (weights, robe chains) -> MPFB hands -> old hand remnants
# -> half-joint helpers -> hidden skull faces. Usage (project folder): scripts/rebuild_mesh.sh   (never after the UV upload went to Meshy)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
export TOKEN=$(cat work/token) BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions
W=$here/work
scripts/B.sh clean_mer.py $here/../mm6_mer1_codex/work/round2/raw_parts.blend $here/../mm9_highwayman_claude/source/true/highwayman1_true.glb $W/clean_v1.blend $W/clean_v1.json | cut -c1-200
scripts/B.sh fit_mer.py $W/clean_v1.blend $here/scripts/fit_mer.json $W/fit_v1.blend $W/fit_v1.json $here/source/nb_hw.glb | cut -c1-120
scripts/B.sh rig_mer.py $W/fit_v1.blend $W/rig_v1.blend $W/rig_v1.json | cut -c1-200
scripts/B.sh graft_hands.py $here/scripts/graft_mer.json | grep -E "^GRAFT|FAILED" | cut -c1-300
scripts/B.sh hands_fix.py $W/hands_v1.blend $W/hands_v2.blend
scripts/B.sh helpers_thf.py $W/hands_v2.blend $W/helpers_v1.blend
scripts/B.sh prune_hidden.py $W/helpers_v1.blend $W/pruned_v1.blend
