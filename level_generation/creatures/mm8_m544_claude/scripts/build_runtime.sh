#!/usr/bin/env bash
# Rebuild the selected textured master without new generation jobs.
set -euo pipefail
project=level_generation/creatures/mm8_m544_claude
token=${1:?Usage: build_runtime.sh LEASE_TOKEN [--install]}
guard=(python3 tools/creature_workspace.py run --project "$project" --token "$token" --)
blender=(tools/run_creature_blender.sh --token "$token")
"${blender[@]}" "$project/scripts/reweight_joints.py"
"${blender[@]}" "$project/scripts/export_unicorn.py"
"${guard[@]}" python3 tools/prepare_actor_glb.py "$project/export/mm8_m544_lod0.glb" "$project/export/mm8_m544_prepared.glb"
"${blender[@]}" "$project/scripts/verify_motion.py"
"${blender[@]}" "$project/scripts/check_horn_socket.py"
"${blender[@]}" "$project/scripts/build_lods.py"
"${guard[@]}" python3 "$project/scripts/shrink_shadow_lods.py" "$project/export/mm8_m544_lods.glb" "$project/export/mm8_m544_shadow.glb"
"${guard[@]}" python3 level_generation/creatures/claude_shared/region_variants.py "$project/export/mm8_m544_shadow.glb" "$project/export/mm8_m544.glb" "$project/textures/unicorn_ramps.json" --extra Unicorn_A openyamm_specular=1 --extra Unicorn_A openyamm_specular_mask=true --extra Unicorn_A pbr.metallicFactor=0
"${blender[@]}" "$project/scripts/export_audit.py"
"${guard[@]}" python3 "$project/scripts/static_audit.py"
"${guard[@]}" python3 "$project/scripts/prepare_viewer.py"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$project/export/mm8_m544.glb"
if [[ ${2:-} == --install ]]; then
    python3 tools/install_model.py "$project/export/mm8_m544.glb" --world mm8
fi
