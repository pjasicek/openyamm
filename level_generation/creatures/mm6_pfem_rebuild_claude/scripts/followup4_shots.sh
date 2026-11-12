#!/usr/bin/env bash
# Follow-up 4 (face defects): installed-before (work/before_followup4, tag inst4) vs fixed (installed, tag fix4) review-viewer shots at
# identical cameras, all three tiers -> review/followup4/{before,after}/ and review/followup4/sheet_*.png. Usage: scripts/followup4_shots.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; repo="$(cd -- "$here/../../.." && pwd)"
G=$here/../claude_shared/gltf_venv/bin/python; S=$repo/level_generation/creatures/claude_shared/texpass_viewer_shots.py
SPECS=("front:Standing:1.0:front:head:0,1.57,0.32:0,1.57,0.03"
       "quarterR_low:Standing:1.0:front:head:-0.16,1.50,0.18:-0.05,1.53,0.0"
       "quarterL_low:Standing:1.0:front:head:0.16,1.50,0.18:0.05,1.53,0.0"
       "sideR:Standing:1.0:front:head:-0.36,1.55,0.02:0,1.55,0.0"
       "sideL:Standing:1.0:front:head:0.36,1.55,0.02:0,1.55,0.0"
       "below:Standing:1.0:front:head:0,1.30,0.26:0,1.56,0.02"
       "back:Standing:1.0:front:head:0.12,1.53,-0.40:0,1.53,0.0"
       "backL_low:Standing:1.0:front:head:0.30,1.40,-0.28:0,1.52,-0.03"
       "forehead:Standing:1.0:front:head:0.0,1.60,0.25:0,1.60,0.07"
       "nose:Standing:1.0:front:head:-0.09,1.50,0.20:-0.01,1.545,0.07"
       "jawR:Standing:1.0:front:head:-0.22,1.42,0.12:-0.03,1.50,0.03"
       "walkR_low:Walk2:0.225:front:head:-0.16,1.50,0.18:-0.05,1.53,0.0"
       "walkSideL:Walk2:0.6:front:head:0.36,1.55,0.02:0,1.55,0.0")
mkdir -p review/followup4/before review/followup4/after
for tag in inst4 fix4; do
  dir=before; [ $tag = fix4 ] && dir=after
  $G -W ignore scripts/viewer_manifest.py $tag followup4 > /dev/null
  (cd "$repo" && python3 $S shots $here $here/review/followup4/$dir pfem_a_$tag,pfem_b_$tag,pfem_c_$tag "${SPECS[@]}" | tail -3)
  for f in review/followup4/$dir/pfem_?_${tag}_*.png; do b=${f##*/}; t=${b%%_${tag}_*}; mv "$f" review/followup4/$dir/${t}_${b##*_${tag}_}; done
done
python3 $S sheet review/followup4/sheet_face_tierA.png review/followup4/before review/followup4/after pfem_a front,quarterR_low,quarterL_low,below,forehead,nose,jawR
python3 $S sheet review/followup4/sheet_face_tiers.png review/followup4/before review/followup4/after pfem_a,pfem_b,pfem_c front,quarterR_low,quarterL_low,nose
python3 $S sheet review/followup4/sheet_sides_back.png review/followup4/before review/followup4/after pfem_a,pfem_b,pfem_c sideR,sideL,back,backL_low
python3 $S sheet review/followup4/sheet_walk.png review/followup4/before review/followup4/after pfem_a,pfem_b,pfem_c walkR_low,walkSideL
