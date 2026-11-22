#!/usr/bin/env bash
# Scorpion runtime GLB: compose -> grade -> gutter fill (every map) -> ramps -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> skin scorpion_a (region ramps) -> far LODs
# (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/) -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose_scorpion.py
python3 ../claude_shared/grade_basecolor.py --ao textures/scorpion_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/scorpion_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/scorpion_upload.glb textures/scorpion_basecolor_graded.png \
  textures/scorpion_region_mask.png textures/scorpion_normal_1k.png textures/scorpion_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_scorpion_lod0.glb export/xeen_scorpion_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_scorpion_runtime_lod0.glb" "$here/export/xeen_scorpion_lods.glb" \
  --mesh-node Scorpion
python3 scripts/shrink_shadow_lods.py export/xeen_scorpion_lods.glb export/xeen_scorpion_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_scorpion_lods_shadowfix.glb export/xeen_scorpion_prelod.glb \
  textures/scorpion_ramps.json --extra Scorpion openyamm_specular=0 --extra Scorpion pbr.metallicFactor=0
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=scorpion LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_scorpion_prelod.glb xeen_scorpion | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/scorpion/xeen_scorpion/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/scorpion/xeen_scorpion/installed.glb \
  lodrepair/work/scorpion/xeen_scorpion/$step.glb | tail -1
cp lodrepair/work/scorpion/xeen_scorpion/$step.glb export/xeen_scorpion.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_scorpion.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_scorpion.glb --world xeen
fi
ls -la export/xeen_scorpion.glb
