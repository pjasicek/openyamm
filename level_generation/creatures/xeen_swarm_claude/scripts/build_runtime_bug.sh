#!/usr/bin/env bash
# Doom Bug runtime GLB: gutter fill (last step on every map) -> export -> prepare -> LODs -> shadow fix ->
# A/B/C skins (region ramps) -> winding check. Install separately (tools/install_model.py --world xeen), then the far
# LOD repair (LOD_PLAYBOOK.md). Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 ../claude_shared/gutter_fill.py texturing/bug_upload.glb textures/bug_basecolor_graded.png \
  textures/bug_region_mask.png textures/bug_normal_1k.png textures/bug_mr_1k.png --in-place
python3 scripts/tier_ramps_bug.py > /dev/null
scripts/step.sh export_bug.py
python3 "$repo/tools/prepare_actor_glb.py" export/xeen_doombug_lod0.glb export/xeen_doombug_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/xeen_doombug_runtime_lod0.glb" \
  "$here/export/xeen_doombug_lods.glb" --mesh-node Bug 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods_bug.py export/xeen_doombug_lods.glb export/xeen_doombug_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/xeen_doombug_lods_shadowfix.glb export/xeen_doombug.glb \
  textures/bug_ramps.json --extra Bug openyamm_specular=0 --extra Bug pbr.metallicFactor=0
rm -f export/xeen_doombug_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/xeen_doombug.glb | tail -1
ls -la export/xeen_doombug.glb
