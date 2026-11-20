#!/usr/bin/env bash
# MM9 cow runtime GLB (from mm9_wolf_claude): prepare -> LODs -> shadow fix -> tier skins (region ramps) -> floor pass -> winding check.
# Usage: scripts/build_runtime.sh [--install]; build_export.py and the compose step run before this (README "Rebuild").
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_cow; node=Cow
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 ../claude_shared/region_variants.py export/${name}_lods_shadowfix.glb export/${name}_skins.glb \
  textures/cow_ramps.json --extra $node openyamm_specular=0 --extra $node pbr.metallicFactor=0
# Floor rule with low-passed root shifts (scripts/floor_smooth.py, not floor_fix.py's per-key grounding): loops on the
# floor, run/attack/hit never below it, the corpse on it.
python3 scripts/floor_smooth.py export/${name}_skins.glb export/${name}.glb --loop Standing --loop Walking --loop Running \
  --raise Fidget --raise Hit --ground-death Death Dead
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
