#!/usr/bin/env bash
# MM7 dragonfly runtime GLB from work/uv_master.blend: export -> material contract -> prepare -> LODs -> shadow fix ->
# shared-skin tiers -> viewer tiers -> winding check. No install (batch H rule).
set -euo pipefail
project=level_generation/creatures/mm7_m186_claude
token=${1:?Usage: build_runtime.sh LEASE_TOKEN}
cd "$(dirname "$0")/../../../.."
guard=(python3 tools/creature_workspace.py run --project "$project" --token "$token" --)
blender=(tools/run_creature_blender.sh --token "$token")
"${blender[@]}" "$project/scripts/export_glb.py"
"${guard[@]}" python3 "$project/scripts/material_contract.py" "$project/export/mm7_m186_lod0.glb"
"${guard[@]}" python3 tools/prepare_actor_glb.py "$project/export/mm7_m186_lod0.glb" "$project/export/mm7_m186_runtime_lod0.glb"
"${blender[@]}" "$project/scripts/build_lods.py"
"${guard[@]}" python3 "$project/scripts/shrink_shadow_lods.py" "$project/export/mm7_m186_lods.glb" "$project/export/mm7_m186_shadow.glb"
"${guard[@]}" python3 level_generation/creatures/claude_shared/region_variants.py "$project/export/mm7_m186_shadow.glb" \
  "$project/export/mm7_m186.glb" "$project/textures/dfly_ramps.json" --extra Dragonfly_ openyamm_specular=1 \
  --extra Dragonfly_ openyamm_specular_mask=true --extra Dragonfly_ pbr.metallicFactor=0
rm -f "$project/export/mm7_m186_lods.geometry.glb"
"${guard[@]}" python3 "$project/scripts/viewer_tiers.py" "$project/export/mm7_m186.glb"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$project/export/mm7_m186.glb"
