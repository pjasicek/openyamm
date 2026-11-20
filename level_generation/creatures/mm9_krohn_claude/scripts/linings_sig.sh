#!/usr/bin/env bash
# Linings behind the open rims of the painted master (after work/geo_v2.blend: midline weld + mouth relax) -> work/linings_v1.blend.
# Geometry is added only (existing faces, UVs, weights unchanged). One skin, no region mask: textures/sig_lining_mask.png labels
# every texel region R, so rim_lining.py takes the darkest quarter of each band's own paint.
#   1. neck_cap.py: the head shell's open neck bottom inside the mail collar
#   2. hair_lining.py: inner twin of the hair faces of the head shell (part 3: behind y 0.0 or above z 0.76): under the long hair
#      the view meets the hair's culled back faces
#   3. rim_lining.py: mail collar, short sleeve ends, hauberk hem, the bracer ends at the wrist (cuff_trim ring), boot tops
# Usage (repo root): level_generation/creatures/mm9_sigmund_claude/scripts/linings_sig.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_sigmund_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/sig_lining_mask.png $T/sig_tp_basecolor_graded.png $T/sig_tp_metal_rough_1k.png "${@:3}" | cut -c1-300; }
"$BL" "NECK_CAP|Error|Trace" $rel/scripts/neck_cap.py $W/${SRC:-geo_v2}.blend $W/linings_s1.blend $T/sig_tp_head_basecolor.png | cut -c1-200
HAIR_YMIN=0.0 HAIR_ZMIN=0.76 "$BL" "HAIR_LINING|Error|Trace" $rel/scripts/hair_lining.py $W/linings_s1.blend $W/linings_s2.blend \
  $T/sig_tp_head_basecolor.png 3 0.0015 15 | cut -c1-200
RL linings_s2 linings_s3 bones=Neck,Head,Spine3 band_bones=Neck,Head,Spine,Clavicle depth=0.25 region=R zmin=0.3 inner_offset=0.0005
RL linings_s3 linings_s4 bones=Spine,Pelvis,Thigh,XCOM,x band_bones=Spine,Pelvis,Thigh,XCOM,x depth=0.15 region=R zmin=-0.35 zmax=0.05 \
  min_edges=12 inner_offset=0.0005
RL linings_s4 linings_s5 bones=Calf,Foot band_bones=Calf,Foot,Thigh,Toe depth=0.30 region=R mid_ok=1 inner_offset=0.0005
RL linings_s5 linings_s6 bones=UpperArm,Clavicle band_bones=UpperArm,Clavicle,Spine depth=0.25 region=R zmin=0.2 min_edges=10 \
  mid_ok=1 skip_inner=1
RL linings_s6 linings_v1 bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand depth=0.25 region=R mid_ok=1 inner_offset=0.0005
echo "LININGS done -> $W/linings_v1.blend"
