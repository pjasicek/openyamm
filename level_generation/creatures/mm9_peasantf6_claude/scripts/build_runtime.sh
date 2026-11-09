#!/usr/bin/env bash
# work/half.glb (scripts/rig.sh) -> runtime GLB: prepare -> LODs -> shadow fix -> ramps -> tier head images -> winding -> floor -> mirror -> install.
# Project folder: scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_peasantf6; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
mkdir -p export
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" ${HALF:-work/half.glb} export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node PeasantF6 --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb PeasantF6 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/pf_ramps.json --extra PeasantF6 openyamm_specular=0 --extra PeasantF6 pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
# skirt strips bend up in the fall and corpse only to within 14 cm of the floor (PeasantF5: 14 cm; 8 and 11 cm put the shins through the skirt in Death), then the body is grounded
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_lift.glb $(cat scripts/floor_lift.txt) 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_lift.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
