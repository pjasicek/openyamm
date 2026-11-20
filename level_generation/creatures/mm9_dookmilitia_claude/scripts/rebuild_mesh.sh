#!/usr/bin/env bash
# Meshy returns -> reduced symmetric body -> rest fit -> head -> weights -> hands -> helpers. Usage: scripts/rebuild_mesh.sh   (never after the UV upload went to Meshy)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
rel=level_generation/creatures/$(basename "$here"); TOKEN=$(cat $rel/work/token)
B() { local out log; out=$(tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(CLEAN|FIT|RIG|GRAFT|FINAL|RING|WRIST|HELPERS|OBJ|COIF|SKULL|PART) " "$log" | cut -c1-${W:-300} || true; }
if [[ "${FROM:-}" != fit ]]; then
B $rel/scripts/clean_dook.py $here/meshy/dook_smart_v1/model_urls_glb.glb $here/source/true/dook1_true.glb $here/work/clean_v1.blend $here/work/clean_v1.json
B $rel/scripts/head_prep_dook.py $here/meshy/dook_head_smart_v1/model_urls_glb.glb $here/work/head_parts.blend
fi
B $rel/scripts/fit_dook.py $here/work/clean_v1.blend $here/scripts/fit_dook.json $here/work/fit_v1.blend $here/work/fit_v1.json
B $rel/scripts/graft_head_dook.py $here/work/fit_v1.blend $here/work/head_parts.blend $here/work/graft_v1.blend
B $rel/scripts/rig_dook.py $here/work/graft_v1.blend $here/work/rig_v1.blend $here/work/rig_v1.json
B $rel/scripts/graft_hands.py $here/scripts/graft_dook.json
