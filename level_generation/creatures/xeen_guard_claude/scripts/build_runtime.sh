#!/usr/bin/env bash
# Guard runtime GLB: compose -> grade -> gutter fill (last step on every map) -> ramps -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> skin guard_a (region ramps) -> gem emission
# (red, gentle pulse) -> far LODs (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/)
# -> no emission on the far levels -> winding check. --install: tools/install_model.py --world xeen.
# Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose.py 1.25
python3 ../claude_shared/grade_basecolor.py --ao textures/guard_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/guard_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/guard_upload.glb textures/guard_basecolor_graded.png \
  textures/guard_region_mask.png textures/guard_normal_1k.png textures/guard_mr_1k.png \
  textures/guard_emission_mask.png --in-place
python3 scripts/tier_ramps.py
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_guard_lod0.glb export/xeen_guard_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_guard_runtime_lod0.glb" "$here/export/xeen_guard_lods.glb" \
  --mesh-node Guard
python3 scripts/shrink_shadow_lods.py export/xeen_guard_lods.glb export/xeen_guard_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_guard_lods_shadowfix.glb export/xeen_guard_skin.glb \
  textures/guard_ramps.json --extra Guard pbr.metallicFactor=0
python3 ../claude_shared/emission.py export/xeen_guard_skin.glb export/xeen_guard_prelod.glb --material Guard \
  --mask textures/guard_emission_mask.png --color 0.95,0.06,0.04 --strength 0.9 --pulse 0.2,2.4
rm -f export/xeen_guard_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=guard LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_guard_prelod.glb xeen_guard | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/guard/xeen_guard/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/guard/xeen_guard/installed.glb \
  lodrepair/work/guard/xeen_guard/$step.glb | tail -1
python3 scripts/far_emission.py lodrepair/work/guard/xeen_guard/$step.glb export/xeen_guard.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_guard.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_guard.glb --world xeen
fi
ls -la export/xeen_guard.glb
