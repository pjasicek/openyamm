#!/usr/bin/env bash
# MM9 hen / rooster runtime GLB (from mm9_wolf_claude): prepare -> LODs -> shadow fix -> material extras (one skin, no
# tiers: specular 0, metallic 0) -> floor pass (ground rule) -> winding check. Usage: scripts/build_runtime.sh [--install]
# build_export.py and compose_chicken.py run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
n="$(basename "$here" | cut -d_ -f2)"; name=mm9_$n; node="${n^}"
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 scripts/drop_lod_slivers.py export/${name}_lods_shadowfix.glb export/${name}_lods_clean.glb
python3 scripts/set_material_extras.py export/${name}_lods_clean.glb export/${name}_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
# Floor (claude_shared/floor/README.md, ground rule): stand/walk/idle on the floor, run/attack/hit never below it,
# the corpse on it.
F=../claude_shared/floor/floor_fix.py
python3 $F export/${name}_extras.glb export/${name}.glb --ground-loop Standing --ground-loop Walking \
  --ground-loop Fidget --raise-uniform Running --raise AttackMelee --raise Hit --ground-death Death Dead \
  --smooth-loop Walking 0.05 --smooth AttackMelee 0.06 --smooth Hit 0.06 --smooth Death 0.08
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
