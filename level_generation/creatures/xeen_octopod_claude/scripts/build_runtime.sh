#!/usr/bin/env bash
# Octopod runtime GLB: compose -> grade -> gutter fill (last step on every map) -> ramps -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> skins octopod_a/b/c (region ramps)
# -> far LODs (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/) -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose.py
python3 ../claude_shared/grade_basecolor.py --ao textures/octopod_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/octopod_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/octopod_upload.glb textures/octopod_basecolor_graded.png \
  textures/octopod_region_mask.png textures/octopod_normal_1k.png textures/octopod_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_octopod_lod0.glb export/xeen_octopod_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_octopod_runtime_lod0.glb" "$here/export/xeen_octopod_lods.glb" \
  --mesh-node Octopod
python3 scripts/shrink_shadow_lods.py export/xeen_octopod_lods.glb export/xeen_octopod_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_octopod_lods_shadowfix.glb export/xeen_octopod_prelod.glb \
  textures/octopod_ramps.json --extra Octopod openyamm_specular=0 --extra Octopod pbr.metallicFactor=0 --extra Foam openyamm_specular=0 --extra Foam pbr.metallicFactor=0
rm -f export/xeen_octopod_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=octopod LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_octopod_prelod.glb xeen_octopod | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/octopod/xeen_octopod/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/octopod/xeen_octopod/installed.glb \
  lodrepair/work/octopod/xeen_octopod/$step.glb | tail -1
cp lodrepair/work/octopod/xeen_octopod/$step.glb export/xeen_octopod.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_octopod.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_octopod.glb --world xeen
fi
ls -la export/xeen_octopod.glb
