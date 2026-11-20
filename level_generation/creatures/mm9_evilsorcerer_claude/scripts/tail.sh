#!/usr/bin/env bash
# Mesh + textures -> GLB -> clips -> half joints -> panels -> runtime. Usage (project folder): TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_evilsorcerer; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; M=work/uv_tex.npz
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/es_ramps.json --extra Sorcerer openyamm_specular=0 --extra Sorcerer pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore scripts/add_sockets.py export/${n}_floor.glb export/${n}_sock.glb 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_sock.glb export/${n}.glb 2>&1 | tail -1
rm -f export/${n}_lods.geometry.glb
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
