#!/usr/bin/env bash
# MM9 Greater Demon runtime GLB (from mm9_lobber_claude): prepare -> LODs -> shadow fix -> material extras -> floor
# pass (ground rule) -> winding check. Usage: scripts/build_runtime.sh [--install]
# build_export.py and compose.py run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_greaterdemon; node=GreaterDemon
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node ${LOD_ARGS:-} 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 scripts/set_material_extras.py export/${name}_lods_shadowfix.glb export/${name}_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
# Floor (claude_shared/floor/README.md, ground rule): standing/walk on the floor, run/attacks/hit never below it, the
# corpse on it. The MM9 clips stand 0.165 m lower than the bind pose (knees bent), so every living clip first moves up
# by the standing depth (HOVER, from clip_heights.py); the tail, which MM9 drags through the floor in the attacks,
# bends up from its own joints instead of lifting the body; then the usual ground/raise/corpse passes.
HOVER="${HOVER:-$(python3 scripts/clip_heights.py export/${name}_extras.glb | awk '$1=="Standing"{printf "%.6f", -$5}')}"
echo "standing lift $HOVER"
F=../claude_shared/floor/floor_fix.py
python3 $F export/${name}_extras.glb export/${name}_lift.glb --hover "$HOVER" Death Dead
python3 $F export/${name}_lift.glb export/${name}.glb --lift-joints Fidget AttackMelee AttackRanged Hit Running Walking \
  --lift-only 'Xtail*' --ground-loop Standing --ground-loop Walking --raise Running --raise Fidget \
  --raise AttackMelee --raise AttackRanged --raise Hit --ground-death Death Dead
python3 scripts/fix_winding.py export/${name}.glb export/${name}_wound.glb && mv export/${name}_wound.glb export/${name}.glb
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
