#!/usr/bin/env bash
# Witch runtime GLBs from the gated master: grade -> tier ramps -> gutter fill (last step on every map) -> clips synced
# into the UV master (rig_v5 -> rig_v6) -> export -> prepare -> LODs -> shadow fix -> A/B/C skins (one region: the
# robe) -> staff split into its attachment -> crystal emission on the staff -> winding check.
# --install: tools/install_model.py --world xeen for body and staff. Far LODs: LOD playbook ladder afterwards.
# Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
P=level_generation/creatures/$(basename "$here")
python3 ../claude_shared/grade_basecolor.py --ao textures/witch_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 \
  --contrast 1.06 --saturation 1.15 textures/witch_basecolor.png
python3 scripts/tier_ramps.py | cut -c1-300
python3 ../claude_shared/gutter_fill.py texturing/witch_upload.glb textures/witch_basecolor_graded.png \
  textures/witch_region_mask.png textures/witch_normal_1k.png textures/witch_mr_1k.png --in-place
(cd "$repo" && scripts_dir="$P/scripts" && "$here/scripts/step.sh" sync_actions.py "$P/work/rig_v5.blend" "$P/work/rig_v6.blend")
(cd "$repo" && "$here/scripts/step.sh" export_runtime.py)
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_witch_lod0.glb export/xeen_witch_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_witch_runtime_lod0.glb" \
  "$here/export/xeen_witch_lods.glb" --mesh-node Witch 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/xeen_witch_lods.glb export/xeen_witch_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_witch_lods_shadowfix.glb export/xeen_witch.glb textures/witch_ramps.json \
  --extra Witch openyamm_specular=0 --extra Witch pbr.metallicFactor=0 \
  --extra Staff openyamm_specular=0.4 --extra Staff pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/xeen_witch.glb --joint Staff --body export/xeen_witch.glb \
  --attachment export/xeen_witch_staff.glb
python3 ../claude_shared/emission.py export/xeen_witch_staff.glb export/xeen_witch_staff.glb --material Staff \
  --mask textures/staff_emission_mask.png --color 1.0,0.25,0.85 --strength 1.6 --pulse 0.2,2.4
for f in export/xeen_witch.glb export/xeen_witch_staff.glb; do
  python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$f" | tail -1
done
if [[ "${1:-}" == "--install" ]]; then
  for name in xeen_witch xeen_witch_staff; do
    python3 "$repo/tools/install_model.py" "export/$name.glb" --world xeen
  done
fi
ls -la export/xeen_witch.glb export/xeen_witch_staff.glb
