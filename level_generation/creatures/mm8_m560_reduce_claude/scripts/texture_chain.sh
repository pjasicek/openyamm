#!/usr/bin/env bash
# Rebuilt + retextured wyvern runtime: compose -> skinned geometry (uv_master.blend) -> swap into the creature's own
# LOD0 export -> prepare (glTF normal convention) -> LODs (creature's ratios, 4 influences) -> region variants
# (tier ramps) -> material classes to ORM -> export/mm8_m560.glb. Usage: texture_chain.sh
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(cd ../../.. && pwd); SH=../claude_shared
python3 scripts/compose.py
REA_CLIPS=0 blender -b -P scripts/export_rebuild.py -- work/rt_geom.glb uv_master.blend 2>&1 | grep -E "EXPORTED|Error"
python3 scripts/swap_rt.py work/rt_geom.glb work/rt_lod0.glb
python3 "$REPO/tools/prepare_actor_glb.py" work/rt_lod0.glb work/rt_prepared.glb
blender -b --python "$REPO/tools/build_actor_lods.py" -- "$PWD/work/rt_prepared.glb" "$PWD/work/rt_lods.glb" \
    --mesh-node Wyvern --max-influences 4 2>&1 | grep -iE "LOD triangles|error" || true
python3 $SH/region_variants.py work/rt_lods.glb work/rt_regions.glb textures/wyvern_ramps.json
mkdir -p textures/runtime
python3 $SH/material_classes_to_orm.py work/rt_regions.glb export/mm8_m560.glb --classes textures/wyvern_material_classes.png \
    --report review/material_orm.json --maps-dir textures/runtime
echo CHAIN done
