#!/usr/bin/env bash
# Unreduced source GLB from work/uv_master.blend with the robot chain: export -> material contract -> prepare -> LODs
# (0.5/0.25/0.125, 4 influences) -> shadow fix -> shared-skin tiers (tint factors, glow ramps; compose_v2.py) ->
# work/mm7_m386_source.glb (ladder input and
# rollback). Usage: build_source.sh LEASE_TOKEN
set -euo pipefail
project=level_generation/creatures/mm7_m386_v2_claude
token=${1:?Usage: build_source.sh LEASE_TOKEN}
cd "$(dirname "$0")/../../../.."
guard=(python3 tools/creature_workspace.py run --project "$project" --token "$token" --)
blender=(tools/run_creature_blender.sh --token "$token")
"${blender[@]}" "$project/scripts/export_glb.py" work/uv_master.blend work/source_lod0.glb
"${guard[@]}" python3 "$project/scripts/material_contract.py" "$project/work/source_lod0.glb"
"${guard[@]}" python3 tools/prepare_actor_glb.py "$project/work/source_lod0.glb" "$project/work/source_runtime_lod0.glb"
"${blender[@]}" "$project/scripts/build_lods.py" work/source_runtime_lod0.glb work/source_lods.glb
"${guard[@]}" python3 "$project/scripts/shrink_shadow_lods.py" "$project/work/source_lods.glb" "$project/work/source_shadow.glb"
"${guard[@]}" python3 level_generation/creatures/claude_shared/region_variants.py "$project/work/source_shadow.glb" \
  "$project/work/mm7_m386_source.glb" "$project/textures/robot_ramps.json" --extra Robot_ openyamm_specular=1 \
  --extra Robot_ 'openyamm_specular_occlusion="orm"' --extra Robot_ pbr.metallicFactor=1
"${guard[@]}" python3 "$project/scripts/tier_factors.py" "$project/work/mm7_m386_source.glb"
rm -f "$project/work/source_lods.geometry.glb"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$project/work/mm7_m386_source.glb"
