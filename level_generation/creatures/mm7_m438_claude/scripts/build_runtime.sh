#!/usr/bin/env bash
# m438 runtime GLBs from the gated, textured master (adapted from mm7_m190_claude): clips synced from rig_v5 into rig_v6
# -> export -> prepare -> LODs -> shadow fix -> colour variants (trousers + headband) -> severed forearm split into an
# attachment -> head merged into the body. No install (batch F keeps everything in the project); the install commands
# are in the README. Token: CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
P=level_generation/creatures/mm7_m438_claude
B() { (cd "$repo" && tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}") | sed -n 's/^Blender log: //p' | xargs grep -hE "SYNC|PROP|STUMP|CAPLOOPS|EXPORTED|RASTER|^AO|Error|Traceback" | cut -c1-200 || true; }
cd "$here"
[ "${SKIP_SYNC:-}" ] || B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
if [[ "${TEXTURES:-1}" == 1 ]]; then
  B uv_raster.py "$here/work/rig_v6.blend" UVMap 1024
  B uv_raster.py "$here/work/rig_v6.blend" HeadUV 1024
  B bake_ao_natm.py "$here/work/rig_v6.blend" 1024
  python3 scripts/bone_patch.py
  B stump_bone.py "$here/work/rig_v6.blend" "$here/work/rig_v7.blend"
  python3 scripts/compose_m438.py | grep -E "SKIN|CLASSES|NATIVE|RAMPS|WOUND|RIM|BONE"
  # the severed forearm from the textured master (its UVs), own 512 layout, texels copied triangle by triangle
  B make_forearm.py "$here/work/rig_v6.blend"
  B forearm_uv.py dump
  python3 scripts/forearm_textures.py
  B forearm_uv.py apply
else
  # the right-arm stump: Smart Topology's four rods replaced by two broken bone shafts (review 2026-10-20)
  B stump_bone.py "$here/work/rig_v6.blend" "$here/work/rig_v7.blend"
fi
PROP_SIDE=L B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m438_lod0.glb export/mm7_m438_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m438_runtime_lod0.glb" \
  "$here/export/mm7_m438_lods.glb" --mesh-node Zombie 2>&1 | grep "LOD triangles"
MESH_NODE=Zombie python3 scripts/shrink_shadow_lods.py export/mm7_m438_lods.glb export/mm7_m438_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m438_lods_shadowfix.glb export/mm7_m438.glb textures/m438_ramps.json \
  --extra Zombie openyamm_specular=1 --extra Zombie openyamm_specular_mask=true --extra Zombie pbr.metallicFactor=0 \
  --extra Forearm openyamm_specular=1 --extra Forearm openyamm_specular_mask=true --extra Forearm pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m438.glb --joint Sword --body export/mm7_m438.glb \
  --attachment export/mm7_m438_forearm.glb
python3 scripts/clamp_lod_uv.py export/mm7_m438.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m438.glb export/mm7_m438.glb
rm -f export/mm7_m438_lods.geometry.glb
ls -la export/mm7_m438.glb export/mm7_m438_forearm.glb
