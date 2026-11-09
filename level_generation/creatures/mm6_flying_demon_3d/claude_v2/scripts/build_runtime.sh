#!/usr/bin/env bash
# Flying demon runtime GLB: tier exports -> prepare -> LODs -> variants -> (install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../../.." && pwd)"
blender=/snap/bin/blender
for t in a b c; do
  "$blender" --background "$here/work/animated.blend" --python "$here/scripts/export_glb.py" -- "$t" 2>&1 | grep EXPORTED
done
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_wdm_a.glb" "$here/export/mm6_wdm_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_wdm_runtime_lod0.glb" \
  "$here/export/mm6_wdm_lods.glb" --mesh-node Flying_Demon 2>&1 | grep "LOD triangles"
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_wdm_b.glb" "$here/export/mm6_wdm_b_png.glb" >/dev/null
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_wdm_c.glb" "$here/export/mm6_wdm_c_png.glb" >/dev/null
python3 "$here/scripts/merge_variants.py" "$here/export/mm6_wdm_lods.glb" "$here/export/mm6_wdm_b_png.glb" \
  "$here/export/mm6_wdm_c_png.glb" "$here/export/mm6_wdm.glb"
rm -f "$here/export/mm6_wdm_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_wdm.glb" "$repo/assets_dev/worlds/mm6/models/mm6_wdm.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_wdm.glb"
fi
