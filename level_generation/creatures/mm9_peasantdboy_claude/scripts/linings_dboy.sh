#!/usr/bin/env bash
# Linings behind the open rims of the painted master (see-through gate r1), after the last geometry step
# (work/geo_v2.blend: midline weld + mouth relax) -> work/linings_v1.blend (the build default). Geometry is added only.
#   1. neck_cap.py: the head shell's open neck bottom inside the tunic collar
#   2. hair_lining.py: the bob's three hair shells (parts 4, 5, 8) get a flipped inner twin on a dark hair texel (under the
#      bob the view met the hair's culled back faces at the neck sides)
#   3. rim_lining.py collar (Neck/Head rims above z 0.2, band 20 cm) and the trouser tops (z -0.2..0, band 12 cm) on a dark
#      texel of the embroidered band region (G); the forearm end at the wrist (cuff_trim.py's ring, band 25 cm up the arm)
#      on a leather texel of the belt region (A): its rim strip reads as the wrist band's edge, not a hollow cuff
# Usage (repo root): level_generation/creatures/mm9_peasantdboy_claude/scripts/linings_dboy.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_peasantdboy_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/pdboy_region_mask.png $T/pdboy_tp_basecolor_graded.png $T/pdboy_tp_metal_rough_1k.png "${@:3}" | cut -c1-260; }
"$BL" "NECK_CAP|Error|Trace" $rel/scripts/neck_cap.py $W/${SRC:-geo_v2}.blend $W/linings_s1.blend \
  $T/pdboy_tp_head_basecolor.png | cut -c1-200
"$BL" "HAIR_LINING|Error|Trace" $rel/scripts/hair_lining.py $W/linings_s1.blend $W/linings_s2.blend \
  $T/pdboy_tp_head_basecolor.png 4,5,8 0.0015 15 | cut -c1-200
RL linings_s2 linings_s3 bones=Neck,Head,Spine3 band_bones=Neck,Head,Spine,Clavicle depth=0.20 region=G zmin=0.2 \
  inner_offset=0.0005
RL linings_s3 linings_s4 bones=Spine,Pelvis,Thigh band_bones=Spine,Pelvis,Thigh depth=0.12 region=G zmin=-0.22 zmax=0.0 \
  min_edges=12 inner_offset=0.0005
RL linings_s4 linings_v1 bones=UpperArm,Forearm band_bones=Forearm,UpperArm,Clavicle,Spine depth=0.25 \
  region=A dark_pct=40 mid_ok=1 inner_offset=0.0005
# 4. sleeve_twin.py: the shoulder/sleeve tunic faces (UpperArm, Clavicle, Forearm, |x| > 0.10) not yet lined get a flipped
#    inner twin (r3: in AttackMelee the view through the raised arm's armpit met the shoulder's culled back faces)
# 5. mouth_fill.py: the mouth pocket closed (head geometry, positions only)
"$BL" "SLEEVE_LINING|Error|Trace" $rel/scripts/sleeve_twin.py $W/linings_v1.blend $W/linings_v2.blend \
  $T/pdboy_tp_basecolor_graded.png UpperArm,Clavicle,Forearm 0.10 0.0015 10 | cut -c1-200
"$BL" "MOUTH_FILL|Error|Trace" $rel/scripts/mouth_fill.py $W/linings_v2.blend $W/linings_v3.blend | cut -c1-200
echo "LININGS done -> $W/linings_v3.blend"
