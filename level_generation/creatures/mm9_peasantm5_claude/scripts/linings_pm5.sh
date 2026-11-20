#!/bin/bash
# Linings behind the open garment rims (see-through gate, 2026-11-02; PeasantDM2's linings.sh tools, project folder):
# head neck bottom capped (neck_cap.py; capping the 19-edge neck loop too made 8 inverted closed parts: left open), the shirt's rims at the belt lined (band 12 cm), the cuffs lined (sleeve band 55 cm,
# Meshy's inner sleeve layer skipped). Geometry added only (existing faces, UVs, weights unchanged): paints stay valid.
set -euo pipefail
cd "$(dirname "$0")/.."
W=$PWD/work; T=$PWD/textures; IN=${1:-$W/fit_m5_ds.blend}
B="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python"
RL() { $B scripts/rim_lining.py -- "$1" "$2" "${2%.blend}.json" $T/pm5_region_mask.png $T/pm5_tp_basecolor_graded.png $T/pm5_tp_metal_rough_1k.png "${@:3}" 2>&1 | grep -E "RIM_LINING|Error|Trace" | cut -c1-200; }
$B scripts/neck_cap.py -- "$IN" $W/lin_s1.blend $T/pm5_tp_head_basecolor.png 2>&1 | grep -E "NECK_CAP|Error|Trace" | cut -c1-200
RL $W/lin_s1.blend $W/lin_s2.blend bones=Spine,Bone band_bones=Spine,Pelvis,Bone,Thigh depth=0.12 region=R zmin=-0.1 zmax=0.25 min_edges=20 inner_offset=0.0005
RL $W/lin_s2.blend $W/linings_v1.blend bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand,Clavicle,Spine,Neck depth=0.55 region=R mid_ok=1 skip_inner=1
echo "LININGS done -> $W/linings_v1.blend"
