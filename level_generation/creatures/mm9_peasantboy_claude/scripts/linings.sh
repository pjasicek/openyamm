#!/usr/bin/env bash
# Linings behind every open garment rim of the painted master (PeasantDM2's step 7b), positions/faces only: the paid
# paints and every existing UV stay valid. work/ears_v1.blend -> work/linings_v1.blend (the build default).
# Rims (Blender rest, pelvis-centred, floor -0.4825): head shell neck bottom (0.615, 30 edges), belt shells (0.16-0.31,
# 30-34 edges), boot tops (-0.143) and ankle rims (-0.367), sleeve cuffs (|x| 0.464), sleeve tops in the armholes
# (|x| 0.13, z 0.535). Our mask channels: R vest, G sleeves, B trousers, A belt (boots are in no channel).
# Usage (repo root): scripts/linings.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_peasantboy_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/pboy_region_mask.png $T/pboy_tp_basecolor_graded.png $T/pboy_tp_metal_rough_1k.png "${@:3}" | cut -c1-260; }
"$BL" "NECK_CAP|Error|Trace" $rel/scripts/neck_cap.py $W/${SRC:-ears_v1}.blend $W/linings_s1.blend \
  $T/pboy_tp_head_basecolor.png | cut -c1-200
RL linings_s1 linings_s2 bones=Spine,Pelvis band_bones=Spine,Pelvis,Thigh depth=0.12 region=R zmin=0.1 zmax=0.35 \
  min_edges=12 inner_offset=0.0005
RL linings_s2 linings_s3 bones=Calf,Foot band_bones=Calf,Foot,Thigh,Toe,Pelvis depth=0.30 region=B mid_ok=1 \
  band_regions=B inner_offset=0.0005
RL linings_s3 linings_s4 bones=UpperArm,Clavicle band_bones=UpperArm,Clavicle depth=0.10 region=G zmin=0.45 \
  min_edges=12 inner_offset=0.0005
RL linings_s4 linings_v1 bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand,Clavicle,Spine,Neck depth=0.55 \
  region=G mid_ok=1 skip_inner=1
echo "LININGS done -> $W/linings_v1.blend"
