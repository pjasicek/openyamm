#!/usr/bin/env bash
# Armadillo runtime GLB: compose -> grade -> ramps -> gutter fill (last step on every map) -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> skin armadillo_a (region ramps) -> far LODs
# (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/) -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose_dillo.py
python3 ../claude_shared/grade_basecolor.py --ao textures/dillo_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/dillo_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/dillo_upload.glb textures/dillo_basecolor_graded.png \
  textures/dillo_region_mask.png textures/dillo_normal_1k.png textures/dillo_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_armadillo_lod0.glb export/xeen_armadillo_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_armadillo_runtime_lod0.glb" "$here/export/xeen_armadillo_lods.glb" \
  --mesh-node Dillo
python3 scripts/shrink_shadow_lods.py export/xeen_armadillo_lods.glb export/xeen_armadillo_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_armadillo_lods_shadowfix.glb export/xeen_armadillo_prelod.glb \
  textures/dillo_ramps.json --extra Dillo openyamm_specular=0 --extra Dillo pbr.metallicFactor=0
rm -f export/xeen_armadillo_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=dillo LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_armadillo_prelod.glb xeen_armadillo | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/dillo/xeen_armadillo/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/dillo/xeen_armadillo/installed.glb \
  lodrepair/work/dillo/xeen_armadillo/$step.glb | tail -1
cp lodrepair/work/dillo/xeen_armadillo/$step.glb export/xeen_armadillo.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_armadillo.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_armadillo.glb --world xeen
fi
ls -la export/xeen_armadillo.glb
