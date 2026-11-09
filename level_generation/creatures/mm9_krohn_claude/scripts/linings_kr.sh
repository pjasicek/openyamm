#!/usr/bin/env bash
# Linings behind the open rims of the painted master (see-through gate r3: the bracer ends at the wrist 150-180 px in every frame,
# the skirt hems and the tabard from below in Death/Dead up to 990 px). Geometry is added only (rim_lining.py, from
# mm9_sigmund_claude); one skin: textures/kr_lining_mask.png labels every texel region R, so each band takes the darkest quarter of
# its own paint. work/grip_v1.blend -> work/linings_v1.blend (then add_props.py -> work/grip_props_cape.blend).
# Usage (repo root): level_generation/creatures/mm9_krohn_claude/scripts/linings_kr.sh
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
rel=level_generation/creatures/mm9_krohn_claude
P=$repo/$rel; W=$P/work; T=$P/textures
BL="$P/scripts/bl.sh"
RL() { "$BL" "RIM_LINING|Error|Trace" $rel/scripts/rim_lining.py "$W/$1.blend" "$W/$2.blend" "$W/$2.json" \
  $T/kr_lining_mask.png $T/kr_tp_basecolor_graded.png $T/kr_tp_metal_rough_1k.png "${@:3}" | cut -c1-300; }
RL ${SRC:-grip_v1} lin_s1 bones=Forearm,Hand band_bones=Forearm,UpperArm,Hand depth=0.3 region=R mid_ok=1 offset=0.004 inner_offset=0.0005
RL lin_s1 lin_s2 bones=Spine,Pelvis,Thigh,Yfront,Yback band_bones=Spine,Pelvis,Thigh,Yfront,Yback depth=0.25 region=R zmin=-0.8 zmax=0.05 min_edges=12 offset=0.004 inner_offset=0.0005
RL lin_s2 linings_v1 bones=Calf,Foot band_bones=Calf,Foot,Thigh,Toe depth=0.35 region=R mid_ok=1 offset=0.004 inner_offset=0.0005
echo "LININGS done -> $W/linings_v1.blend"
