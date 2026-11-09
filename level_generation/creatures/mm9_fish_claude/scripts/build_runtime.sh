#!/usr/bin/env bash
# MM9 fish runtime GLB (from mm9_crow_claude): prepare -> LODs -> shadow fix -> fins out of the shadow meshes ->
# material settings (fin MASK) -> floor
# pass (swimmer lift; README "Swimming") -> winding check. Usage: scripts/build_runtime.sh [--install]
# build_export.py and compose_fish.py run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_fish; node=Fish
python3 scripts/set_extras.py export/${name}_lod0.glb export/${name}_lod0_opaque.glb --opaque-fins
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0_opaque.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 scripts/strip_shadow_fins.py export/${name}_lods_shadowfix.glb export/${name}_lods_nofinshadow.glb $node
python3 scripts/set_extras.py export/${name}_lods_nofinshadow.glb export/${name}_extras.glb
# Floor (claude_shared/floor/README.md, swimmer rule since 2026-11-04: monster_data Fly = S, MM9's AISwimFly): the
# clips keep MM9's body, its origin at the centre of the MM9 body box (FISH dims half-height 16 LT = 0.4096 m here), so
# a fish centred in its water is drawn where MM9 draws it; the death eases into the corpse on its side on the floor (it
# sinks to the bed). The ground rule before it lifted the living clips +0.018 (lowest fin tip on the floor).
HOVER="${HOVER:-0.4096}"
echo "swim lift $HOVER"
F=../claude_shared/floor/floor_fix.py
python3 $F export/${name}_extras.glb export/${name}.glb --swim "$HOVER" Death Dead
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
