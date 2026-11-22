#!/usr/bin/env bash
# Insect Swarm runtime GLB: gutter fill (last step on every map) -> export -> prepare -> LODs -> shadow fix ->
# A/B/C skins (region ramps) -> winding check. Install separately (tools/install_model.py --world xeen), then the far
# LOD repair (LOD_PLAYBOOK.md). Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 ../claude_shared/gutter_fill.py texturing/wasp_upload.glb textures/wasp_basecolor_graded.png \
  textures/wasp_region_mask.png textures/wasp_normal_1k.png textures/wasp_mr_1k.png --in-place
python3 scripts/tier_ramps.py > /dev/null
scripts/step.sh export_glb.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_swarm_lod0.glb export/xeen_swarm_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_swarm_runtime_lod0.glb" \
  "$here/export/xeen_swarm_lods.glb" --mesh-node Swarm 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/xeen_swarm_lods.glb export/xeen_swarm_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_swarm_lods_shadowfix.glb export/xeen_swarm.glb \
  textures/wasp_ramps.json --extra Swarm openyamm_specular=0 --extra Swarm pbr.metallicFactor=0
rm -f export/xeen_swarm_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_swarm.glb | tail -1
ls -la export/xeen_swarm.glb
