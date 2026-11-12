#!/usr/bin/env bash
# MM6 PeasantF1 rebuild runtime (project folder): work/half.glb (scripts/rig.sh with MESH=work/uv_tex.npz) -> prepare -> LODs -> shadow fix
# -> tiers (region mask + v3 ramps) -> winding -> skirt lift + floor -> mirror (true-handed, as every MM9-route GLB) -> winding check [-> install]
# Usage: scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm6_pfem; G="$here/../claude_shared/gltf_venv/bin/python"; L=../claude_shared
mkdir -p export
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" ${HALF:-work/half.glb} export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node PeasantF1 --max-influences 4 ${LODARGS:-} 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb PeasantF1 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/pfem_ramps.json --extra Peasant openyamm_specular=0 --extra Peasant pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py work/${n}_rv.glb work/${n}_rv2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py work/${n}_rv2.glb work/${n}_lift.glb $(cat scripts/floor_lift.txt) 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py work/${n}_lift.glb work/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore scripts/mirror_glb.py work/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm6 2>&1 | tail -2; fi
ls -la export/${n}.glb
