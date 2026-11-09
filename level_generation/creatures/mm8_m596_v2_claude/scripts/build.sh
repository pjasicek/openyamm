#!/usr/bin/env bash
# Rebuild the Crystal Walker v2 from the prepared Meshy mesh (work/mesh_t7000.blend, prep_mesh.py):
# authored head (new_head.py) -> rig -> UVs -> facet texture -> clips -> runtime maps -> LODs -> winding check.
# Run from the repository root with CREATURE_3D_TOKEN set.
set -euo pipefail
P=level_generation/creatures/mm8_m596_v2_claude
B() { tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$@" > /dev/null; }
B $P/scripts/new_head.py work/mesh_t7000.blend work/mesh_h1.blend
B $P/scripts/rig.py work/mesh_h1.blend work/joints_v2.json work/rig_v2.blend
B $P/scripts/uv.py work/rig_v2.blend work/rig_uv2.blend
python3 $P/scripts/texture.py
B $P/scripts/anim.py work/rig_uv2.blend work/anim_v2.blend work/anim_v2.glb
python3 tools/prepare_actor_glb.py $P/work/anim_v2.glb $P/work/runtime_lod0.glb
B $P/scripts/build_lods.py
rm -f $P/export/mm8_m596.geometry.glb
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $P/export/mm8_m596.glb
