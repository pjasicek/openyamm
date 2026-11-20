#!/usr/bin/env bash
# Linings behind every open garment rim (DM2's step 7b, scripts copied from mm9_peasantdm2_claude), on the last geometry
# step (work/hairtwin_v1.blend: curtain_v2 -> rigid_beard.py -> hair_twin.py) -> work/linings_v1.blend (the build default). Positions/faces only: paints and UVs stay valid.
#   neck cap (the head shell's open neck bottom), collar (tunic neck opening, band 30 cm), belt (tunic rims at the belt, Spine- or Bone22-weighted: the corpse showed the tunic's inside
#   at the belt from under the skirt;
#   min_edges 20: the 12-16 edge loops at the buckle were lined at 12 and collapsed into zero-volume parts in LOD2/3),
#   boots (boot cuff + trouser rims at the knee, band 30 cm), wrists (DM1's cuff_trim ring of the bare forearm over the
#   MPFB hand stub; band 55 cm up the arm to the shoulder as DM2's sleeves, dark tunic texel, inner-layer faces skipped:
#   through the cuff the view reached the tunic sleeve's inside at the elbow, and a 10 cm band left those holes).
# Usage (repo root): scripts/linings.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_peasantdm3_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/pdm3_region_mask.png $T/pdm3_tp_basecolor_graded.png $T/pdm3_tp_metal_rough_1k.png "${@:3}" | cut -c1-240; }
"$BL" "NECK_CAP|Error|Trace" $rel/scripts/neck_cap.py $W/${SRC:-hairtwin_v1}.blend $W/linings_s1c.blend \
  $T/pdm3_tp_head_basecolor.png | cut -c1-200
RL linings_s1c linings_s2 bones=Neck,Head band_bones=Neck,Head,Spine,Clavicle depth=0.30 region=R zmin=0.25 inner_offset=0.0005
RL linings_s2 linings_s3 bones=Spine,Bone band_bones=Spine,Pelvis,Bone,Thigh depth=0.12 region=R zmin=-0.1 zmax=0.1 min_edges=20 \
  inner_offset=0.0005
RL linings_s3 linings_s4 bones=Calf band_bones=Calf,Foot,Thigh,Toe,Bone,Pelvis,Spine depth=0.30 region=A mid_ok=1 \
  band_regions=A inner_offset=0.0005
RL linings_s4 linings_v1 bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand,Clavicle,Spine,Neck depth=0.55 \
  region=R mid_ok=1 skip_inner=1
echo "LININGS done -> $W/linings_v1.blend"
