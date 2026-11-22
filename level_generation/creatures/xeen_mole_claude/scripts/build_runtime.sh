#!/usr/bin/env bash
# Mole runtime GLB: compose -> grade -> ramps -> gutter fill (last step on every map) -> export -> prepare -> LOD1
# (tools/build_actor_lods.py via scripts/lods_wrap.py) -> shadow tuck -> A/B/C skins (region ramps) -> far LODs
# (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/) -> winding check.
# --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose_mole.py
python3 ../claude_shared/grade_basecolor.py --ao textures/mole_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/mole_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/mole_upload.glb textures/mole_basecolor_graded.png \
  textures/mole_region_mask.png textures/mole_normal_1k.png textures/mole_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_mole_lod0.glb export/xeen_mole_runtime_lod0.glb
scripts/step.sh lods_wrap.py "$here/export/xeen_mole_runtime_lod0.glb" "$here/export/xeen_mole_lods.glb" \
  --mesh-node Mole
python3 scripts/shrink_shadow_lods.py export/xeen_mole_lods.glb export/xeen_mole_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_mole_lods_shadowfix.glb export/xeen_mole_prelod.glb \
  textures/mole_ramps.json --extra Mole openyamm_specular=0 --extra Mole pbr.metallicFactor=0
rm -f export/xeen_mole_lods.geometry.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=mole LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py \
  --source export/xeen_mole_prelod.glb xeen_mole | tail -3
step=$($LV -c "import json;print(json.load(open('lodrepair/work/mole/xeen_mole/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/mole/xeen_mole/installed.glb \
  lodrepair/work/mole/xeen_mole/$step.glb | tail -1
cp lodrepair/work/mole/xeen_mole/$step.glb export/xeen_mole.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_mole.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_mole.glb --world xeen
fi
ls -la export/xeen_mole.glb
