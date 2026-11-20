#!/usr/bin/env bash
# Linings behind the open garment rims of PeasantM7's body (see-through gate, 2026-11-02) on this project's master
# work/ears_v4.blend -> work/linings_v1.blend (the build master). rim_lining.py is PeasantDM2's (copied unchanged):
# geometry added only, existing faces/UVs/weights untouched, linings on one dark texel of the band's own region.
#   boots:  both rims at each knee (the boot cuff top and the shaft inside it), band 30 cm (shaft, foot, breeches to the hip)
#   belt:   the two rims where the upper tunic meets the skirt under the belt (z 0.17-0.19, root_bone/Bone02), band 12 cm
# Usage (repo root): level_generation/creatures/mm9_peasantm7d_claude/scripts/linings.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_peasantm7d_claude
P=$repo/$rel; W=$P/work; T=$P/textures
RL() { "$P/scripts/bl.sh" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/pm7d_region_mask.png $T/pm7d_tp_basecolor_graded.png $T/pm7d_tp_metal_rough_1k.png "${@:3}" | cut -c1-220; }
RL ears_v4 linings_s1 bones=Calf band_bones=Calf,Foot,Thigh,Toe depth=0.30 region=B mid_ok=1 inner_offset=0.0005
RL linings_s1 linings_v1 bones=root_bone,Bone0 band_bones=root_bone,Bone0,Spine,Pelvis,Thigh depth=0.12 region=R zmin=0.10 \
  zmax=0.25 min_edges=12 inner_offset=0.0005
# (collar: not lined. The gate found no collar zone holes, and a Spine3 lining of the V/placket rims made four near-zero-volume
#  closed shells that check_winding.py counts as inverted)
echo "LININGS done -> $W/linings_v1.blend"
