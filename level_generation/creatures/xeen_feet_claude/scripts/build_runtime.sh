#!/usr/bin/env bash
# Flying Feet runtime GLB: ramps -> export -> prepare -> LOD1 (+ provisional LOD2/3) -> shadow tuck -> feet_a skin
# (region ramps, specular 0, metallic 0) -> winding check. Textures first (scripts/build_textures.sh); far LODs by the
# LOD playbook ladder afterwards (scripts/far_lods.sh), then install. Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 scripts/tier_ramps.py
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_feet_lod0.glb export/xeen_feet_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_feet_runtime_lod0.glb" \
  "$here/export/xeen_feet_lods.glb" --mesh-node Feet 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/xeen_feet_lods.glb export/xeen_feet_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_feet_lods_shadowfix.glb export/xeen_feet.glb \
  textures/feet_ramps.json --extra Feet openyamm_specular=0 --extra Feet pbr.metallicFactor=0
rm -f export/xeen_feet_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_feet.glb | tail -1
ls -la export/xeen_feet.glb
