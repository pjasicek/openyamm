#!/usr/bin/env bash
# Step 7b (VARIANTS_BRIEF see-through lesson, PeasantDM2's rim_lining.py): linings behind the open garment rims of the
# rigged master, after the last geometry step (work/rigid_v1.blend) -> work/linings_v1.blend (the build default).
# Positions/faces only: the paid paints and every existing UV stay valid. The see-through gate on the unlined build
# (review/gates/see_through_r0/) found: the waist (tunic shell's lower rim and the skirt piece's upper rim under the belt
# part open when bending: torso 317 px), the boot tops (28 / 25 px), sleeves (Death R 121 px), trousers (38 px).
#   1. waist: rims of the tunic shell and the skirt/breeches piece between z 0.10 and 0.32 (Blender rest; belt 0.175-0.24),
#      band 12 cm, tunic texel (region R)
#   2. boots: both rims at each knee (breeches cuff and boot top), band 30 cm, an unmasked (leather/breeches) texel; band
#      faces unmasked only (band_regions G: the neck-skin label never reaches the legs, so only unlabelled faces pass)
#   3. sleeves: every remaining tunic face within 55 cm of the cuff rim, tunic texel, the sleeve's inner layer skipped
# Usage (repo root): scripts/linings_pm3.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_peasantm3_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/pm3_region_mask.png $T/pm3_tp_basecolor_graded.png $T/pm3_tp_metal_rough_1k.png "${@:3}" | cut -c1-260; }
RL rigid_v1 linings_s1 bones=Spine,Pelvis band_bones=Spine,Pelvis,Thigh,Bone depth=0.12 region=R zmin=0.10 zmax=0.32 \
  min_edges=12 inner_offset=0.0005
RL linings_s1 linings_s2 bones=Calf band_bones=Calf,Foot,Thigh,Toe,Pelvis,Spine,Bone depth=0.30 region=none mid_ok=1 \
  band_regions=G inner_offset=0.0005
RL linings_s2 linings_v1 bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand,Clavicle,Spine,Neck depth=0.55 region=R \
  mid_ok=1 skip_inner=1
echo "LININGS done -> $W/linings_v1.blend"
