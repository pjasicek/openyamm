#!/usr/bin/env bash
# Reduced runtime GLB from the picked ladder step (config l, Cand_79): cand_glb.sh (kept normals -> export_cand ->
# swap_lod0 onto the source export) -> floor/top points -> LODs (protected crown rim, horn tips, Death/Dead floor
# contacts) -> shadow LODs inset (the source project's step) -> colour variants carried to every LOD/shadow primitive
# -> sub-texel LOD UV clamp -> winding check. Usage: TOKEN=<lease> scripts/build_reduced.sh [out.glb]
set -euo pipefail
cd "$(dirname "$0")/.."; P=$PWD; out=${1:-export/mm7_m254.glb}; ROOT=$(cd ../../.. && pwd)
REA_KEPT_NORMALS=1 scripts/cand_glb.sh l Cand_79 kn
cp work/glb_l_79kn.glb work/pick_lod0.glb
python3 scripts/spike_points.py
REA_NODE=Golem BL_GREP=FLOOR scripts/bl.sh floor_points.py "$P/work/pick_lod0.glb"
BL_GREP='PROTECTED|LOD triangles' scripts/bl.sh build_lods.py "$P/work/pick_lod0.glb" "$P/work/pick_lods.glb"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb
cp work/pick_lods_shadowfix.glb "$out"; python3 scripts/carry_variants.py "$out"; python3 scripts/clamp_lod_uv.py "$out"
python3 "$ROOT/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$out"
python3 scripts/compare_glb.py work/mm7_m254_source_pre_reduce.glb "$out" | tail -10; ls -la "$out"
