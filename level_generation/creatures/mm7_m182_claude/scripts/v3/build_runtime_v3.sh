#!/bin/bash
# v3 runtime chain (after scripts/v3/build_geometry.sh and scripts/v3/compose_v3.py): geometry export -> swap into the
# installed cdr1 GLB (clips, sockets, materials kept; old LODs dropped) -> burn maps -> v3 maps, ramps, MM7 variant
# names -> LODs (tools/build_actor_lods.py) -> LOD0 wing membranes kept in every LOD -> shadow LODs tucked inside
# -> variant mappings on every LOD -> winding check. Output: export/mm7_m182.glb (+ export/mm7_m182_lod0.glb).
set -euo pipefail
P="$(cd "$(dirname "$0")/../.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
L="$P/work/v3/logs"; mkdir -p "$L"
t(){ local n=$1; shift; "$@" > "$L/$n.txt" 2>&1 || { echo "FAILED $n"; tail -20 "$L/$n.txt"; exit 1; }; tail -1 "$L/$n.txt" | cut -c1-200; }
t export blender -b --factory-startup -P scripts/v3/export_geom.py
t swap python3 scripts/v3/swap_lod0.py work/v3/cdr1_installed.glb work/v3/geom_export.glb work/v3/stage_lod0.glb Body
(cd ../claude_shared && t burn python3 bake_burn_maps.py "$P/work/v3/stage_lod0.glb" "$P/textures/v3/m182v3" --node Body \
  --material DragonBody_A=body --material DragonHead_A=head --material DragonWings_A=wings --open DragonWings_A \
  --fast DragonWings_A=0.5 --ignite Head Tail8 Tail9)
t apply python3 scripts/v3/apply_textures_v3.py work/v3/stage_lod0.glb export/mm7_m182_lod0.glb
t lods blender -b --factory-startup -P "$ROOT/tools/build_actor_lods.py" -- export/mm7_m182_lod0.glb work/v3/lods.glb --mesh-node Body
grep -h "LOD triangles" "$L/lods.txt" || true
t wings python3 scripts/v3/preserve_wing_lods.py work/v3/lods.glb
t shadow python3 scripts/v3/shrink_shadow_lods.py work/v3/lods.glb export/mm7_m182.glb
t variants python3 scripts/v3/carry_variants.py export/mm7_m182.glb
t winding python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm7_m182.glb
sha256sum export/mm7_m182.glb
