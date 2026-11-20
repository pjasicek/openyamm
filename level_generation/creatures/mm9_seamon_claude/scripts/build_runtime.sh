#!/usr/bin/env bash
# MM9 Sea Monster runtime GLB (from mm9_dfly_claude): prepare -> LODs -> shadow fix -> A/B/C skins (region ramps) ->
# floor pass (swimmer lift, corpse grounding) -> winding check. Usage: scripts/build_runtime.sh [--install]
# build_export.py and compose_sea.py run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_seamon; node=Sea
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 ../claude_shared/region_variants.py export/${name}_lods_shadowfix.glb export/${name}_skins.glb \
  textures/sea_ramps.json --extra $node openyamm_specular=0 --extra $node pbr.metallicFactor=0
# Floor (claude_shared/floor/README.md, swimmer rule since 2026-11-04: monster_data Fly = S, MM9's AISwimFly): every
# living clip keeps MM9's motion and carries MM9's origin at the centre of the MM9 body box (SEAMONSTER Dims
# half-height 35 LT = 0.896 m); Death eases from it into the corpse on the floor. Before it the ground rules
# (--ground-loop Standing/Walking, --raise the rest, --ground-death) stood it on its claw tips.
F=../claude_shared/floor/floor_fix.py
python3 $F export/${name}_skins.glb export/${name}.glb --swim 0.896 Death Dead
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
