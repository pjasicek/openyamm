#!/usr/bin/env bash
# Mantis runtime GLB: compose -> grade -> gutter fill (every map) -> ramps -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> skins mantis_a/b/c/lava (region ramps) ->
# lava glow (claude_shared/emission.py on Mantis_LAVA only) -> far LODs (LOD_PLAYBOOK.md ladder, project copy of
# lod_repair_claude/scripts in lodrepair/) -> far emission maps -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose_mantis.py
python3 ../claude_shared/grade_basecolor.py --ao textures/mantis_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/mantis_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/mantis_upload.glb textures/mantis_basecolor_graded.png \
  textures/mantis_region_mask.png textures/mantis_normal_1k.png textures/mantis_mr_1k.png \
  textures/mantis_emission_mask.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_mantis_lod0.glb export/xeen_mantis_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_mantis_runtime_lod0.glb" "$here/export/xeen_mantis_lods.glb" \
  --mesh-node Mantis
python3 scripts/shrink_shadow_lods.py export/xeen_mantis_lods.glb export/xeen_mantis_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_mantis_lods_shadowfix.glb export/xeen_mantis_skins.glb \
  textures/mantis_ramps.json --extra Mantis openyamm_specular=0 --extra Mantis pbr.metallicFactor=0
python3 ../claude_shared/emission.py export/xeen_mantis_skins.glb export/xeen_mantis_prelod.glb --material Mantis_LAVA \
  --mask textures/mantis_emission_mask.png --color 1.0,0.22,0.04 --strength 1.0 --pulse 0.2,2.6
rm -f export/xeen_mantis_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=mantis LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_mantis_prelod.glb xeen_mantis | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/mantis/xeen_mantis/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/mantis/xeen_mantis/installed.glb \
  lodrepair/work/mantis/xeen_mantis/$step.glb | tail -1
python3 scripts/far_emission.py lodrepair/work/mantis/xeen_mantis/$step.glb export/xeen_mantis.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_mantis.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_mantis.glb --world xeen
fi
ls -la export/xeen_mantis.glb
