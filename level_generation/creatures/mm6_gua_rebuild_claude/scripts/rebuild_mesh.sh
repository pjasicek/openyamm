#!/usr/bin/env bash
# Meshy return -> reduced symmetric body -> fit -> weights -> hands. Usage: TOKEN=<lease> scripts/rebuild_mesh.sh   (never after the UV upload went to Meshy)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
rel=level_generation/creatures/$(basename "$here")
B() { local out log; out=$(tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(CLEAN|FIT|RIG|GRAFT) " "$log" | cut -c1-260 || true; }
B $rel/scripts/clean_guard.py $here/meshy/guard_smart_v1/model_urls_glb.glb $here/source/g1/guard1_true.glb $here/work/clean_v2.blend $here/work/clean_v2.json
B $rel/scripts/fit_guard.py $here/work/clean_v2.blend $here/scripts/fit_guard.json $here/work/fit_v1.blend $here/work/fit_v1.json
B $rel/scripts/rig_guard.py $here/work/fit_v1.blend $here/work/rig_v1.blend $here/work/rig_v1.json
B $rel/scripts/graft_hands.py $here/scripts/graft_guard.json
