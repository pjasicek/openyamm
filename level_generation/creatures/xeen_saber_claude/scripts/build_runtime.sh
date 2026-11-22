#!/usr/bin/env bash
# Sabertooth runtime GLB: compose -> grade -> ramps -> gutter fill (last step on every map) -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> the saber_a skin (region ramps) -> far LODs
# (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/) -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose_saber.py
python3 ../claude_shared/grade_basecolor.py --ao textures/saber_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/saber_basecolor.png
python3 scripts/apply_bag.py textures/saber_basecolor_graded.png
python3 ../claude_shared/gutter_fill.py texturing/saber_uvref.glb textures/saber_basecolor_graded.png \
  textures/saber_region_mask.png textures/saber_normal_1k.png textures/saber_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_saber_lod0.glb export/xeen_saber_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_saber_runtime_lod0.glb" "$here/export/xeen_saber_lods.glb" \
  --mesh-node Saber
python3 scripts/shrink_shadow_lods.py export/xeen_saber_lods.glb export/xeen_saber_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_saber_lods_shadowfix.glb export/xeen_saber_prelod.glb \
  textures/saber_ramps.json --extra Saber openyamm_specular=0 --extra Saber pbr.metallicFactor=0
rm -f export/xeen_saber_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=saber LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_saber_prelod.glb xeen_saber | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/saber/xeen_saber/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/saber/xeen_saber/installed.glb \
  lodrepair/work/saber/xeen_saber/$step.glb | tail -1
cp lodrepair/work/saber/xeen_saber/$step.glb export/xeen_saber.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_saber.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_saber.glb --world xeen
fi
ls -la export/xeen_saber.glb
