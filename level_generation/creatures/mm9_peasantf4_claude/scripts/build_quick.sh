#!/bin/bash
# geometry/texture refresh without the paint chain (project folder): finish -> tweak -> chin -> rig -> runtime -> viewer. Usage: scripts/build_quick.sh <rev> [--install]
set -e
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2_tw.npz 0.012 8 > /dev/null
python3 scripts/chin_pf4.py work/uv_tex2_tw.npz work/uv_tex2_chin.npz 16 0.005 | tail -1
python3 scripts/under_hood_pf4.py work/uv_tex2_chin.npz work/uv_tex2.npz work/asm_frozen.npz | tail -1
scripts/rig_f4.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace|GLB|MERGED" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|install|LOD|winding" || true
scripts/viewer_update.sh $1 > /dev/null
echo BUILT $1
