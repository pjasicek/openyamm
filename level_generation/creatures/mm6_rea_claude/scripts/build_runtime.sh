#!/usr/bin/env bash
# Reactor runtime GLB: textures -> geometry/rig -> clips -> export -> material/STEP fix -> prepare -> authored LODs.
# Pass --install to install the accepted GLB with tools/install_model.py (source in assets_source, runtime copy in
# assets_dev). Needs the creature lease token in CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
rel="level_generation/creatures/mm6_rea_claude/scripts"
cd "$repo"
python3 "$here/scripts/paint_textures.py"
for script in build_blend.py anim_reactor.py export_glb.py; do
  tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$rel/$script"
done
python3 "$here/scripts/fix_gltf.py" "$here/export/mm6_rea_lod0.glb" "$here/export/mm6_rea_fixed.glb"
python3 tools/prepare_actor_glb.py "$here/export/mm6_rea_fixed.glb" "$here/export/mm6_rea_runtime_lod0.glb"
# Authored LODs (fewer segments per part) instead of collapse decimation; see author_lods.py.
tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$rel/author_lods.py"
cat "$here/export/lods.json"
if [[ "${1:-}" == "--install" ]]; then
  python3 tools/install_model.py "$here/export/mm6_rea.glb" --world mm6
fi
