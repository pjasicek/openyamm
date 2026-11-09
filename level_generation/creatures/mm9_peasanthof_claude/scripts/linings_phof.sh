#!/usr/bin/env bash
# Linings behind the open garment rims of one master (see-through gate r1, 2026-11-02: up the skirt in Death/Running, into
# the sleeves, the collar), after the last geometry step. Positions/faces only: the paid paints and every UV stay valid.
#   0. sleeve_tuck.py (M7's): the hand stub's deep vertices take the forearm's weights (Death's bent wrist poked 3.7 mm)
#   1. neck_cap.py: the head shell's open neck bottom capped (a neck-skin texel)
#   2. rim_lining.py skirt: every rim weighted to the skirt chains (hem, apron edges), band 0.8 m (the whole skirt), region G
#   3. rim_lining.py collar: the shawl/bodice opening round the neck, band 0.3 m, region R
#   4. rim_lining.py boots: the boot tops (Calf), band 0.3 m
#   5. rim_lining.py sleeves: the short sleeves' rims (UpperArm/Forearm), band 0.4 m, skip_inner
#   6. waist_cap.py: a disc across the inside of the dress at the hips, facing down (the view up the skirt of the corpse)
# Usage (repo root): scripts/linings_phof.sh <in blend> <out blend> <body prefix> <ramps prefix a|c> [z_cap]
set -euo pipefail
rel=level_generation/creatures/mm9_peasanthof_claude
P=$PWD/$rel; S=$rel/scripts; IN=$1; OUT=$2; B=$3; R=$4; ZC=${5:--0.06}
T=$P/textures; W=$(dirname "$OUT"); base=$(basename "$OUT" .blend)
RL() { $S/bld.sh "RIM_LINING|Error|Trace" $S/rim_lining.py "$1" "$2" "${2%.blend}.json" $T/${R}_region_mask.png \
  $T/${B}_basecolor_graded.png $T/${B}_metal_rough_1k.png "${@:3}" | cut -c1-220; }
$S/bld.sh "TUCK|SLEEVE|Error|Trace" $S/sleeve_tuck.py "$IN" $W/${base}_s0.blend 0.82 0.002 1 | cut -c1-200
$S/bld.sh "NECK_CAP|Error|Trace" $S/neck_cap.py $W/${base}_s0.blend $W/${base}_s1.blend $T/${B}_head_basecolor.png | cut -c1-200
RL $W/${base}_s1.blend $W/${base}_s2.blend bones=xbk,xfr,xrt,XCOM band_bones=xbk,xfr,xrt,XCOM,Pelvis,Spine,Thigh depth=${SKIRT_DEPTH:-0.8} region=G mid_ok=1 inner_offset=0.0005
RL $W/${base}_s2.blend $W/${base}_s3.blend bones=Neck,Spine2,Clavicle band_bones=Neck,Head,Spine,Clavicle depth=0.30 region=R zmin=0.35 inner_offset=0.0005
RL $W/${base}_s3.blend $W/${base}_s4.blend bones=Calf band_bones=Calf,Foot,Toe depth=0.30 region=none mid_ok=1 inner_offset=0.0005
RL $W/${base}_s4.blend $W/${base}_s5.blend bones=UpperArm,Forearm band_bones=UpperArm,Forearm,Clavicle depth=0.40 region=none mid_ok=1 skip_inner=1
$S/bld.sh "WAIST_CAP|Error|Trace" $S/waist_cap.py $W/${base}_s5.blend "$OUT" $T/${B}_basecolor_graded.png $ZC | cut -c1-200
echo "LININGS done -> $OUT"
