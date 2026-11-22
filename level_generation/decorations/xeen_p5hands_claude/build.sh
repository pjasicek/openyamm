#!/usr/bin/env bash
# The shrine's stone hands: high (pose, palm closed, forearm, plinth, voxel union) -> LOD0, UVs, bakes -> maps ->
# LODs + export -> linked GLB -> the left hand as its mirror -> winding. Blender through lane S's lock.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
"$blender" --background --factory-startup --python scripts/build_high.py > work/high.log 2>&1
grep -E "FILLED|HIGH |Traceback|Error" work/high.log | cut -c1-200 || true
"$blender" --background --factory-startup --python scripts/lowbake.py > work/lowbake.log 2>&1
grep -E "LOD0|SPARROW best|^UV charts|LOWBAKE_DONE|Traceback" work/lowbake.log | cut -c1-200 || true
python3 scripts/finish_maps.py
"$blender" --background --factory-startup --python scripts/export_hand.py 2>&1 | grep -E "LOD_TRI|EXPORTED|Error|Traceback"
python3 ../../../tools/link_static_model_lods.py work/xeen_deco_stonehand_r_raw.glb export/xeen_deco_stonehand_r.glb
python3 scripts/mirror_glb.py export/xeen_deco_stonehand_r.glb export/xeen_deco_stonehand_l.glb xeen_deco_stonehand_l
for s in r l; do python3 ../mm8_3d/animated/scripts/check_winding.py export/xeen_deco_stonehand_$s.glb | tail -1; done
python3 ../../creatures/claude_shared/texture_quality.py export/xeen_deco_stonehand_r.glb | tail -1
