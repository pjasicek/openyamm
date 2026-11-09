#!/bin/bash
# Job 8 (2026-11-04) geometry rebuild without the paint chain (the r31 textures stay): tweak -> chin -> under hood -> puff -> bust ->
# eyelid -> bodice fix (holes, chevrons, hem spikes) -> rig -> runtime -> viewer. work/asm_frozen.npz already carries sleeve_rings_pf4.py.
# Project folder, under the 12G cap from the caller. Usage: scripts/build_j8.sh <viewer rev> [--install]
set -e
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2_tw.npz 0.012 8 > /dev/null
python3 scripts/chin_pf4.py work/uv_tex2_tw.npz work/uv_tex2_chin.npz 16 0.005 > /dev/null
python3 scripts/under_hood_pf4.py work/uv_tex2_chin.npz work/uv_tex2_uh.npz work/asm_frozen.npz > /dev/null
python3 scripts/puff_pf4.py work/uv_tex2_uh.npz work/uv_tex2_puff.npz work/rig.json ${PUFFKEEP:-0.0} > /dev/null
python3 scripts/bust_pf4.py work/uv_tex2_puff.npz work/uv_tex2_bust.npz
python3 scripts/eyelid_pf4.py work/uv_tex2_bust.npz work/uv_tex2_lid.npz > /dev/null
python3 scripts/bodice_fix_pf4.py work/uv_tex2_lid.npz work/uv_tex2.npz
scripts/rig_f4.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|install|LOD" || true
scripts/viewer_update.sh $1 > /dev/null
echo BUILT $1
