#!/usr/bin/env bash
set -euo pipefail
project=level_generation/creatures/mm8_m488_claude
token=${1:?Usage: build_runtime.sh LEASE_TOKEN [--install]}
guard=(python3 tools/creature_workspace.py run --project "$project" --token "$token" --)
blender=(tools/run_creature_blender.sh --token "$token")
"${guard[@]}" python3 "$project/scripts/compose_textures.py"
"${blender[@]}" "$project/scripts/export_glb.py"
"${guard[@]}" python3 "$project/scripts/material_contract.py" "$project/export/mm8_m488_lod0.glb"
"${guard[@]}" python3 tools/prepare_actor_glb.py "$project/export/mm8_m488_lod0.glb" "$project/export/mm8_m488_runtime_lod0.glb"
"${blender[@]}" "$project/scripts/export_audit.py"
"${blender[@]}" "$project/scripts/build_lods.py"
"${guard[@]}" python3 "$project/scripts/shrink_shadow_lods.py" "$project/export/mm8_m488_lods.glb" "$project/export/mm8_m488_shadow.glb"
"${guard[@]}" python3 level_generation/creatures/claude_shared/region_variants.py "$project/export/mm8_m488_shadow.glb" "$project/export/mm8_m488_variants.glb" "$project/textures/m488_ramps.json" --extra Minotaur openyamm_specular=1 --extra Minotaur openyamm_specular_mask=true --extra Minotaur pbr.metallicFactor=0
"${guard[@]}" python3 tools/merge_head_material.py "$project/export/mm8_m488_variants.glb" "$project/export/mm8_m488.glb"
"${guard[@]}" python3 "$project/scripts/static_audit.py"
"${guard[@]}" python3 "$project/scripts/viewer_tiers.py"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$project/export/mm8_m488.glb"
if [[ ${2:-} == --install ]]; then
    python3 tools/install_model.py "$project/export/mm8_m488.glb" --world mm8
fi
