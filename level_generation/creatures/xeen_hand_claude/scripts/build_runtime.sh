#!/usr/bin/env bash
# Carnage Hand runtime GLB: compose -> grade (local 0: the sparrow pack's 4-texel gutters) -> procedural mouth texels
# back -> gutter fill (last step on every map) -> ramps -> export -> prepare -> LOD1 -> shadow tuck -> skin hand_a
# (region ramps, specular 0, metallic 0) -> far LODs (LOD_PLAYBOOK.md ladder, project copy of
# lod_repair_claude/scripts in lodrepair/) -> winding check. --install: tools/install_model.py --world xeen.
# Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose.py
python3 ../claude_shared/grade_basecolor.py --ao textures/hand_ao_2k.png --fine 1.0 --local 0.0 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/hand_basecolor.png
python3 scripts/keep_procedural.py
python3 ../claude_shared/gutter_fill.py texturing/hand_upload.glb textures/hand_basecolor_graded.png \
  textures/hand_region_mask.png textures/hand_normal_1k.png textures/hand_mr_1k.png --in-place
python3 scripts/tier_ramps.py
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_hand_lod0.glb export/xeen_hand_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_hand_runtime_lod0.glb" \
  "$here/export/xeen_hand_lods.glb" --mesh-node Hand 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/xeen_hand_lods.glb export/xeen_hand_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_hand_lods_shadowfix.glb export/xeen_hand.glb \
  textures/hand_ramps.json --extra Hand openyamm_specular=0 --extra Hand pbr.metallicFactor=0
rm -f export/xeen_hand_lods.geometry.glb
cp export/xeen_hand.glb export/xeen_hand_prelod.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py --source export/xeen_hand_prelod.glb \
  xeen_hand | tail -2
chosen=$($LV -c "import json; print(json.load(open('lodrepair/work/xeen_hand/result.json'))['chosen'])")
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/xeen_hand/installed.glb lodrepair/work/xeen_hand/$chosen.glb | tail -1
cp lodrepair/export/xeen_hand.glb export/xeen_hand.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_hand.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_hand.glb --world xeen
fi
ls -la export/xeen_hand.glb
