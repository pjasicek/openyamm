#!/usr/bin/env bash
# work/half.glb (scripts/rig_sc.sh) -> runtime GLB: prepare -> LODs -> shadow fix -> ramps (robe, two tiers) -> tier head images -> winding ->
# floor -> mirror (true handedness) -> install. Project folder: scripts/build_runtime_sc.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_scholar; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
mkdir -p export
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" ${HALF:-work/half.glb} export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Scholar --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Scholar 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/sc_ramps.json --extra Scholar openyamm_specular=0 --extra Scholar pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images.py work/${n}_rv.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
# the lower legs shrink into the robe once he is down (legs_hide.py; review r9 robe gate); 2026-11-04: their knees are also pulled 30 % toward
# Bip01 Spine between 0.3 and 0.42 s (the shrunken knee blob left the robe front at 0.42-0.5 s: robe gate Death 5/32 2.5 cm -> 2/32 2.4 cm)
"$G" -W ignore scripts/legs_hide.py export/${n}_skins2.glb export/${n}_legs.glb ${LEGSHIDE:-Death:0.05:0.35:0.05:0.3:0.3:0.42 Dead:0:0:0.05:0.3} 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_legs.glb export/${n}_floor.glb $(cat scripts/floor_ops_sc.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
