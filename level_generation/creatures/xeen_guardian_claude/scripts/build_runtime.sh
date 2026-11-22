#!/usr/bin/env bash
# Guardian runtime GLB: compose -> grade -> procedural gem/eye texels back -> ramps -> gutter fill (last step on every
# map) -> export -> prepare -> LODs -> shadow tuck -> skin guardian_a (region ramps) -> emission (gem red, eyes
# green) -> far LODs (LOD_PLAYBOOK.md ladder, project copy of lod_repair_claude/scripts in lodrepair/: the curvature
# step c25_12, the plain r25_12 dropped the eye cores and the gem) -> far emission maps from the far masks -> winding
# check. --install: tools/install_model.py --world xeen. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/compose.py
python3 ../claude_shared/grade_basecolor.py --ao textures/guardian_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/guardian_basecolor.png
python3 scripts/keep_procedural.py
python3 ../claude_shared/gutter_fill.py texturing/guardian_upload.glb textures/guardian_basecolor_graded.png \
  textures/guardian_region_mask.png textures/guardian_normal_1k.png textures/guardian_mr_1k.png \
  textures/guardian_emission_rgb.png --in-place
python3 scripts/tier_ramps.py
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_guardian_lod0.glb export/xeen_guardian_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_guardian_runtime_lod0.glb" \
  "$here/export/xeen_guardian_lods.glb" --mesh-node Skull 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/xeen_guardian_lods.glb export/xeen_guardian_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_guardian_lods_shadowfix.glb export/xeen_guardian_skin.glb \
  textures/guardian_ramps.json --extra Guardian pbr.metallicFactor=0
python3 scripts/emission_rgb.py export/xeen_guardian_skin.glb export/xeen_guardian.glb --material Guardian \
  --image textures/guardian_emission_rgb.png --strength 0.9 --pulse 0.2,2.4
rm -f export/xeen_guardian_lods.geometry.glb
cp export/xeen_guardian.glb export/xeen_guardian_prelod.glb
LV=$repo/level_generation/creatures/lod_repair_claude/venv/bin/python
LOD_REPAIR_RUN=eyes LOD_REPAIR_PYTHON=$LV LOD_RENDER_CULL=1 $LV lodrepair/scripts/repair.py --ladder c0.25/0.125 \
  --source export/xeen_guardian_prelod.glb xeen_guardian | tail -1
$LV lodrepair/scripts/verify_far_only.py lodrepair/work/eyes/xeen_guardian/installed.glb \
  lodrepair/work/eyes/xeen_guardian/c25_12.glb | tail -1
python3 scripts/far_emission.py lodrepair/work/eyes/xeen_guardian/c25_12.glb export/xeen_guardian.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_guardian.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/xeen_guardian.glb --world xeen
fi
ls -la export/xeen_guardian.glb
