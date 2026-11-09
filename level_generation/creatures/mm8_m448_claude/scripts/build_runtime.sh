#!/usr/bin/env bash
# Rebuild from the reviewed rig and cached Meshy returns; no paid calls.
set -euo pipefail
project=level_generation/creatures/mm8_m448_claude
creature_token="${1:?Pass the current creature workspace lease token}"
guard=(python3 tools/creature_workspace.py run --project "$project" --token "$creature_token" --)
"${guard[@]}" python3 "$project/scripts/compose_ratman.py"
tools/run_creature_blender.sh --token "$creature_token" "$project/scripts/export_runtime.py"
"${guard[@]}" python3 tools/prepare_actor_glb.py "$project/export/mm8_ratman_lod0.glb" "$project/export/mm8_ratman_runtime_lod0.glb"
tools/run_creature_blender.sh --token "$creature_token" "$project/scripts/build_lods.py"
"${guard[@]}" python3 "$project/scripts/postprocess_runtime.py"
tools/run_creature_blender.sh --token "$creature_token" "$project/scripts/export_parity.py"
"${guard[@]}" python3 "$project/scripts/verify_runtime.py"
"${guard[@]}" python3 "$project/scripts/viewer_tiers.py"
