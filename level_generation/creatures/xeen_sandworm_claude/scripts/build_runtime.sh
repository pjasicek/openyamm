#!/usr/bin/env bash
# Sand worm runtime GLB: compose -> grade -> gutter fill (last step on every map) -> ramps -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> skins sandworm_a / sandworm_c (region ramps)
# -> far LODs (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/) -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose.py
python3 ../claude_shared/grade_basecolor.py --ao textures/worm_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/worm_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/worm_upload.glb textures/worm_basecolor_graded.png \
  textures/worm_region_mask.png textures/worm_normal_1k.png textures/worm_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_sandworm_lod0.glb export/xeen_sandworm_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_sandworm_runtime_lod0.glb" "$here/export/xeen_sandworm_lods.glb" \
  --mesh-node Worm
python3 scripts/shrink_shadow_lods.py export/xeen_sandworm_lods.glb export/xeen_sandworm_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_sandworm_lods_shadowfix.glb export/xeen_sandworm_prelod.glb \
  textures/worm_ramps.json --extra Worm openyamm_specular=0 --extra Worm pbr.metallicFactor=0
rm -f export/xeen_sandworm_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=worm LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_sandworm_prelod.glb xeen_sandworm | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/worm/xeen_sandworm/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/worm/xeen_sandworm/installed.glb \
  lodrepair/work/worm/xeen_sandworm/$step.glb | tail -1
cp lodrepair/work/worm/xeen_sandworm/$step.glb export/xeen_sandworm.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_sandworm.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_sandworm.glb --world xeen
fi
ls -la export/xeen_sandworm.glb
