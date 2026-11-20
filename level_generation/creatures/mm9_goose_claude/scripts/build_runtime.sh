#!/usr/bin/env bash
# MM9 goose runtime GLB (from mm9_wolf_claude): prepare -> LODs -> shadow fix -> tier skins (region ramps) -> floor
# pass -> winding check. Usage: scripts/build_runtime.sh [--install]
# build_export.py and compose_goose.py run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_goose; node=Goose
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 ../claude_shared/region_variants.py export/${name}_lods_shadowfix.glb export/${name}_skins.glb \
  textures/goose_ramps.json --extra $node openyamm_specular=0 --extra $node pbr.metallicFactor=0
# Floor (claude_shared/floor/README.md, ground rule): standing/walk/idle on the floor, run/attack/hit never below it,
# the corpse on it. Per-key root offsets shook the walk, so they are low-passed (--smooth, brief: no per-frame fixes).
F=../claude_shared/floor/floor_fix.py
python3 $F export/${name}_skins.glb export/${name}.glb --ground-loop Standing --ground-loop Walking \
  --ground-loop Fidget --raise Running --raise AttackMelee --raise Hit --ground-death Death Dead \
  --smooth-loop Walking 0.05 --smooth-loop Running 0.04 --smooth Fidget 0.12 --smooth Hit 0.06 --smooth AttackMelee 0.05
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
