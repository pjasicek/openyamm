#!/usr/bin/env bash
# Neck pass (2026-11-01): work/uv_v3.blend -> work/uv_v4.blend (welded throat: neck_weld.py, harmonic weights: neck_weights.py)
# and the tube's paint (neck_paint.py into the *_graded base, normal and ORM; then grade_regions.py makes the finals).
# Then: TOKEN=<lease> MASTER=work/uv_v4.blend scripts/rebuild.sh [--install]. Usage (project folder): TOKEN=<lease> scripts/neck_pass.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(HEAD|SKIN|LOOPS|TUBE|CAVITY|DUMPED|APPLIED)" "$log" | cut -c1-200 || true; }
mkdir -p work/neck work/neck_in
for f in ldemon_basecolor_graded.png ldemon_basecolor_final.png ldemon_head_basecolor_graded.png ldemon_head_basecolor_final.png ldemon_normal_1k.png ldemon_metal_rough_1k.png ldemon_region_mask.png; do
  [ -f work/neck_in/$f ] || cp textures/$f work/neck_in/$f          # the untouched pass-2 textures, kept once
done
B "$rel/scripts/neck_weld.py" "$here/work/uv_v3.blend" "$here/work/neck/weld.blend"
B "$rel/scripts/neck_dump.py" "$here/work/neck/weld.blend" "$here/work/neck/weld.npz"
"$G" scripts/neck_weights.py work/neck/weld.npz work/neck/weld_w.npz 2>&1 | grep -v Unexpected
B "$rel/scripts/neck_apply_weights.py" "$here/work/neck/weld.blend" "$here/work/neck/weld_w.npz" "$here/work/uv_v4.blend"
"$G" scripts/neck_paint.py work/neck/weld.npz 2>&1 | grep -E "^PAINT|Traceback|Error"
"$G" scripts/grade_regions.py 2>&1 | grep -E "^GRADED|Traceback|Error"
