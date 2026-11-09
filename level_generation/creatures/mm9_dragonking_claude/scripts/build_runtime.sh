#!/usr/bin/env bash
# MM9 Dragon King runtime GLB (from mm9_lobber_claude/mm9_dfly_claude): prepare -> LODs -> shadow fix -> material
# classes (specular/roughness per texel) -> floor pass -> winding check. Usage: scripts/build_runtime.sh [--install]
# build_export.py and compose_dragon.py run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_dragonking; node=DragonKing
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node $node --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb $node
python3 ../claude_shared/material_classes_to_orm.py export/${name}_lods_shadowfix.glb export/${name}_mat.glb \
  --classes textures/dragonking_material_classes.png --head-classes textures/dragonking_head_material_classes.png \
  --report work/material_classes_report.json
# Floor (claude_shared/floor/README.md). The Dragon King flies (canFly) but stands, attacks, casts and dies on the
# ground in MM9; only its travel (Walking/Running = the MM9 fly loop) is airborne. Tail strips first (the stand
# loop swishes the tail tip into the floor), then the stand on the floor, every other living clip never below it
# (the fly loop's wing downstroke lifts the body instead of cutting the floor), the corpse on the floor.
F=../claude_shared/floor/floor_fix.py
# Pass 1: MM9's ground poses hold our (Meshy) hind feet 0.229 above the floor (the toes rest higher than MM9's
# thin ones): every clip but Death/Dead moves down by that amount.
python3 $F export/${name}_mat.glb work/${name}_floor1.glb --hover -0.2289 Death Dead
# Pass 2: the tail strips bend out of the floor (the stand loop swishes the tail tip into it), stand on the floor, every other living clip never below it (the fly loop's wing downstroke lifts the
# body instead of cutting the floor), the corpse on the floor.
python3 $F work/${name}_floor1.glb export/${name}.glb \
  --lift-joints Standing Fidget AttackMelee AttackRanged Cast Hit Taunt Land Death Dead --lift-only 'Xtail*' \
  --ground-loop Standing \
  --raise Fidget --raise AttackMelee --raise AttackRanged --raise Cast --raise Hit --raise Taunt --raise Land \
  --raise-uniform Walking --raise-uniform Running \
  --ground-death Death Dead
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
V="$repo/level_generation/props/mm9_isleofashes_claude/work/venv/bin/python"
$V scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
