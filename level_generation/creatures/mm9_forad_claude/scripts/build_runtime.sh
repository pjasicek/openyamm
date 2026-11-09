#!/usr/bin/env bash
# Runtime GLB: textured master -> MM9 clips -> prepare -> LODs -> shadow fix -> material extras -> corpse grounding
# -> winding check [-> install --world mm9]. Usage: PYGLTF_PYTHON=<python with pygltflib> scripts/build_runtime.sh
#   <prefix> <MeshName> [--install]     (after scripts/rebuild_rig.sh, reduce_uv.py, the retexture and compose.py)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
n="$1"; N="$2"; V="${PYGLTF_PYTHON:?set PYGLTF_PYTHON}"
B="/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1"
$B --python scripts/build_export.py -- work/uv_v1.blend work/${n}_body_tex.glb "$N" "$n" 2>&1 | grep -E "EXPORTED|Error"
"$V" scripts/clips_mm9.py work/${n}_body_tex.glb export/mm9_${n}_lod0.glb scripts/roles_$n.json work/clips_v1.json
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
$B --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
python3 scripts/set_material_extras.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras.glb export/mm9_${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead
rm -f export/mm9_${n}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${3:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9
fi
ls -la export/mm9_${n}.glb
