#!/usr/bin/env bash
# From the LOD glb on: ramps, tier images, floor, sockets, mirror. Project folder. scripts/tail.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_monk; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/mk_ramps.json --extra Monk openyamm_specular=0 --extra Monk pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -1
"$G" -W ignore scripts/add_sockets.py export/${n}_floor.glb export/${n}_sock.glb 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_sock.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -1; fi
