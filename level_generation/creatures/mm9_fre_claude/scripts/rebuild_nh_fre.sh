#!/bin/bash
# Pass 7 (new head) rebuild, project folder, under the 12G memory cap: head textures -> assembly -> rig + clips -> runtime -> viewer.
# Usage: scripts/rebuild_nh_fre.sh <viewer rev> [--install]
# Fixed inputs (never regenerated here): work/uv_tex2.npz + work/weights.npz (r72's final body positions/UVs/weights, rebuild_fre.sh r72),
# the r72 body/braid textures (textures/pf_body_*, fre_hair_*), work/nh/head_geo.npz (nh_build.py), work/nh/head_uv.npz (nh_uv.py: the paid
# layout, never re-run), textures/nh_head_ao.png (texpass_bake_ao.py + pad_ao.py on texturing/fre_newhead_upload.glb).
set -eo pipefail
python3 scripts/nh_textures.py | tail -1
python3 scripts/nh_braid_tone.py | tail -1
python3 scripts/nh_assemble.py | tail -1
scripts/rig_nh_fre.sh 2>&1 | grep -E "Error|Trace|GLB" || true
scripts/build_runtime_fre.sh $2 2>&1 | grep -E "WINDING|winding|Error|Trace|install|LOD" || true
scripts/viewer_update.sh $1 > /dev/null
echo REBUILT $1
