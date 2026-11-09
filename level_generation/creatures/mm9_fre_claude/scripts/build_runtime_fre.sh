#!/usr/bin/env bash
# Fre: work/half.glb (scripts/rig_fre.sh) -> runtime GLB: prepare -> LODs -> shadow fix -> material extras (one skin, no tiers, as Markel)
# -> winding -> floor -> mirror (MM9's true handedness) -> winding check -> [install]. Project folder: scripts/build_runtime_fre.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_fre; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
mkdir -p export
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" ${HALF:-work/half.glb} export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Fre --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Fre 2>&1 | tail -1
"$G" -W ignore scripts/set_material_extras.py export/${n}_lods_shadowfix.glb export/${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/double_hair_fre.py export/${n}_extras.glb export/${n}_extras_d.glb 2>&1 | tail -1      # pass 4: FreHair doubleSided
"$G" -W ignore scripts/fix_winding.py export/${n}_extras_d.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_lift.glb $(cat scripts/floor_lift.txt) 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_lift.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
