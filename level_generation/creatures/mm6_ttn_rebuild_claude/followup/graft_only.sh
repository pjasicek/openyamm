#!/usr/bin/env bash
# graft + bake + compose only (the --graft part of build_runtime.sh), then splice: TOKEN=<lease> followup/graft_only.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
rel=level_generation/creatures/$(basename "$here")
PY=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
B() { local out log; out=$(cd "$repo" && BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(GRAFT|BAKED|LOD triangles)" "$log" | cut -c1-300 || true; }
cd "$here"
B $rel/scripts/graft_ttn.py $rel/scripts/graft_ttn.json
B $rel/scripts/bake_hands_ttn.py work/graft_v1.blend middleage_caucasian_male/middleage_lightskinned_male_diffuse.png
python3 scripts/compose_ttn.py
$PY scripts/splice_ttn.py work/before_rebuild/mm6_ttn.glb work/graft_v1.glb work/splice_v1.glb 2>&1 | grep -v RuntimeWarning | cut -c1-300
