#!/usr/bin/env bash
# Runtime GLB (project folder): rig stage -> prepare -> LODs -> shadow fix -> region ramps -> eye glow -> winding fix -> sockets -> mirror_glb.py
# -> winding check [-> install]. Usage: scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_lichking; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared
UVNPZ=work/uv_tex.npz bash scripts/rig_stage.sh | tail -1
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" work/rig_out.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/work/${n}_lods.glb" --mesh-node LichKing --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py work/${n}_lods.glb work/${n}_lods_shadowfix.glb LichKing 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py work/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/lk_ramps.json --extra LichKing openyamm_specular=0 --extra LichKing pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore $L/emission.py work/${n}_rv.glb work/${n}_glow0.glb --material LichKingHead --mask textures/lk_eye_mask.png --color 1.0,0.13,0.03 --strength 2.2 --pulse 0.12,2.3 2>&1 | tail -1
"$G" -W ignore $L/emission.py work/${n}_glow0.glb work/${n}_glow.glb --material LichKingStaffSkull --mask textures/lk_eye_mask.png --color 0.25,1.0,0.2 --strength 1.6 --pulse 0.12,2.3 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py work/${n}_glow.glb work/${n}_wind.glb 2>&1 | tail -1
"$G" -W ignore scripts/add_sockets.py work/${n}_wind.glb work/${n}_sock.glb 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py work/${n}_sock.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
