#!/usr/bin/env bash
# Rebuild from the selected UV/animation master without another generation job.
set -euo pipefail
project=level_generation/creatures/mm8_m408_claude
token=${1:?Usage: build_runtime.sh LEASE_TOKEN [--install]}
guard=(python3 tools/creature_workspace.py run --project "$project" --token "$token" --)
blender=(tools/run_creature_blender.sh --token "$token")
"${blender[@]}" "$project/scripts/export_glb.py"
"${guard[@]}" python3 tools/prepare_actor_glb.py "$project/export/mm8_m408_lod0.glb" "$project/export/mm8_m408_runtime_lod0.glb"
"${blender[@]}" "$project/scripts/export_audit.py"
"${blender[@]}" "$project/scripts/build_lods.py"
"${guard[@]}" python3 "$project/scripts/shrink_shadow_lods.py" "$project/export/mm8_m408_lods.glb" "$project/export/mm8_m408_shadow.glb"
"${guard[@]}" python3 level_generation/creatures/claude_shared/region_variants.py "$project/export/mm8_m408_shadow.glb" "$project/export/mm8_m408.glb" "$project/textures/m408_ramps.json" --extra Couatl openyamm_specular=1 --extra Couatl openyamm_specular_mask=true --extra Couatl pbr.metallicFactor=0
"${guard[@]}" python3 "$project/scripts/static_audit.py"
"${guard[@]}" python3 "$project/scripts/viewer_tiers.py"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$project/export/mm8_m408.glb"
if [[ ${2:-} == --install ]]; then
    python3 tools/install_model.py "$project/export/mm8_m408.glb" --world mm8
fi
