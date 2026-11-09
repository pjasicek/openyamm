#!/usr/bin/env bash
# PeasantDM4: PeasantDM2's step 7b on work/tuck_trim.blend, regions from scripts/lining_regions.py. DM2's notes:
# Step 7b (2026-11-02, user: "holes in sleeves + some in knees (e.g. running anim 12)"): linings behind every open garment
# rim of the painted master, after the last geometry step (work/eyes_relax_fix.blend) -> work/linings_v1.blend (the
# build default). Positions/faces only: the paid paints and every existing UV stay valid.
#   1. (no forearm extension: sleeve_lining.py's continuation of the tucked hand stub up the sleeve poked out of the back
#      of the sleeve at the elbow in the rest pose, 10-28 mm, at 6 or 9 cm from the elbow; the lining behind the stub
#      closes the view instead)
#   2. neck_cap.py: the head shell's open neck bottom (inside the tunic) capped with a fan on a neck-skin texel; then
#      rim_lining.py collar: the tunic's neck opening, band 30 cm (the upper chest and back: at 12 cm the lying corpse
#      showed the unlined mid-back through the collar)
#   3. rim_lining.py belt: the tunic's rims at the belt (four loops; the knot's 10-edge opening left open), band 12 cm
#      (the skirt's faces weighted to the skirt ring's Bone22 and the hips' faces with thigh-weighted corners included)
#   4. rim_lining.py boots: both rims at each knee (trouser piece ending in the turned-down cuff; the boot shaft inside
#      it), band 30 cm: the whole shaft and the foot (its few large faces; views down the bent knee reach the ankle) and
#      the trousers up to the hip (their thigh weights go partly to the skirt ring's Bone22; trouser and boot texels
#      only, not the tunic skirt); boot leather, region B
#   5. rim_lining.py cuffs: every remaining tunic face within 55 cm of the cuff rim (the whole sleeve, the shoulder and
#      the torso side next to it), lined on one dark texel of the tunic paint, cuff rim strip; the sleeve's own inner
#      layer (faces facing the arm) is not lined (skip_inner: its twins showed as dark patches outside the sleeve)
# Usage (repo root): scripts/linings.sh   (lease token from LEASE_TOKEN.txt via scripts/bl.sh)
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_peasantdm4_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/pdm4_lining_regions.png $T/pdm4_tp_basecolor_graded.png $T/pdm4_tp_metal_rough_1k.png min_lum=0.06 "${@:3}" | cut -c1-200; }
# collar, belt, boots: vertices of Meshy's inner-layer faces (folds facing the body axis) do not move: the twin lies on the
# face, back to back (at 3 mm, and in posed folds even at 0.5 mm, their
# twins poked through the fold's outer layer as dark specks on the skirt)
# rims first, the sleeves' wide band last: a later band leaves out faces an earlier one lined, and only the run that
# lines a rim's faces can join that rim to its lining
"$BL" "NECK_CAP|Error|Trace" $rel/scripts/neck_cap.py $W/tuck_trim.blend $W/linings_s1c.blend \
  $T/pdm4_tp_head_basecolor.png | cut -c1-200
RL linings_s1c linings_s2 bones=Neck,Head band_bones=Neck,Head,Spine,Clavicle depth=0.30 region=R zmin=0.25 \
  inner_offset=0.0005
RL linings_s2 linings_s3 bones=Spine band_bones=Spine,Pelvis,Bone,Thigh depth=0.12 region=R zmin=-0.1 zmax=0.1 min_edges=12 \
  inner_offset=0.0005
RL linings_s3 linings_s4 bones=Calf band_bones=Calf,Foot,Thigh,Toe,Bone,Pelvis,Spine depth=0.30 region=B mid_ok=1 \
  band_regions=BG inner_offset=0.0005
# PeasantDM4: the puffed outer sleeves end at the elbow in their own open rims (15-19 edges, UpperArm/Forearm): lined
# before the wrist band, which would otherwise line their faces without joining them to the elbow rim
RL linings_s4 linings_s4b bones=UpperArm,Forearm band_bones=UpperArm,Forearm,Clavicle,Spine depth=0.25 region=R mid_ok=1 \
  skip_inner=1 min_edges=12 max_edges=19
# PeasantDM4: the cuff lining takes shaded linen (pick_rgb; the darkest texel read as a black ring round the wrist from
# the front); inner-layer faces of the undersleeves get own-paint 0.5 mm twins (skip_inner left the bottom wall of
# the trimmed right cuff unlined: background through the cuff in every clip, 58-146 px)
RL linings_s4b linings_s5 bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand,Clavicle,Spine,Neck depth=0.55 \
  region=R mid_ok=1 inner_offset=0.0005 pick_rgb=0.45,0.37,0.28
# PeasantDM4: the tunic skirt's hem (two loops on the skirt bones Bone*, z -0.2) and its belt-level rims (four loops on
# Bone22/Spine near z 0, which DM2's Spine-only belt run does not select), then the cap's inner lining (cap_lining.py:
# the Meshy cap shell has gaps and an open rim)
RL linings_s5 linings_s6 bones=Bone band_bones=Bone,Spine,Thigh depth=0.25 region=R zmax=-0.1 mid_ok=1 inner_offset=0.0005
RL linings_s6 linings_s7 bones=Bone,Spine band_bones=Bone,Spine,Thigh depth=0.12 region=R zmin=-0.1 zmax=0.1 min_edges=12 \
  mid_ok=1 inner_offset=0.0005
"$BL" "CAP|Error|Trace" $rel/scripts/cap_lining.py $W/linings_s7.blend $W/linings_v1.blend | cut -c1-200
echo "LININGS done -> $W/linings_v1.blend"
