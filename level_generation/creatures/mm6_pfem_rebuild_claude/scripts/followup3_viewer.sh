#!/usr/bin/env bash
# Follow-up 3 (head posture): installed (work/before_followup3) vs candidate viewer shots at identical cameras, tier A, side and
# three-quarter per clip -> review/followup3/{installed,fixed}/ and review/followup3/sheet_*.png. Usage: scripts/followup3_viewer.sh <candidate glb>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; repo="$(cd -- "$here/../../.." && pwd)"
G=$here/../claude_shared/gltf_venv/bin/python; S=$repo/level_generation/creatures/claude_shared/texpass_viewer_shots.py
CAND=${1:-work/followup3/cand.glb}; T=pfem_a
SPECS=("standR:Standing:1.0:right:body" "walk0R:Walk2:0.0:right:body" "walk1R:Walk2:0.225:right:body" "walk2R:Walk2:0.45:right:body"
       "walk3R:Walk2:0.675:right:body" "walk1Q:Walk2:0.225:quarter:body" "walk3Q:Walk2:0.675:quarter:body" "walkH:Walk2:0.225:right:head"
       "run1R:Running:0.2:right:body" "run2R:Running:0.55:right:body" "run1Q:Running:0.2:quarter:body"
       "fid1R:Fidget:1.0:right:body" "fid2R:Fidget:2.0:right:body" "fid1Q:Fidget:2.0:quarter:body"
       "att1R:Attack:0.3:right:body" "att2R:Attack:0.48:right:body" "att1Q:Attack:0.48:quarter:body"
       "hit1R:Hit:0.3:right:body" "hit1Q:Hit:0.3:quarter:body"
       "standH:Standing:1.0:right:head:0.75,1.56,0.0:0,1.52,-0.02" "walk1H:Walk2:0.225:right:head:0.75,1.56,0.0:0,1.52,-0.02"
       "walk3H:Walk2:0.675:right:head:0.75,1.56,0.0:0,1.52,-0.02" "run1H:Running:0.2:right:head:0.75,1.56,0.0:0,1.52,-0.02")
mkdir -p review/followup3/installed review/followup3/fixed
$G -W ignore scripts/viewer.py work/before_followup3/mm6_pfem.glb inst3 | tail -1
$G -W ignore scripts/viewer.py "$CAND" fix3 | tail -1
for tag in inst3 fix3; do
  dir=installed; [ $tag = fix3 ] && dir=fixed
  $G -W ignore scripts/viewer_manifest.py $tag followup3 > /dev/null
  (cd "$repo" && python3 $S shots $here $here/review/followup3/$dir ${T}_$tag "${SPECS[@]}" | tail -1)
  for f in review/followup3/$dir/${T}_${tag}_*.png; do mv "$f" review/followup3/$dir/${T}_${f##*_${tag}_}; done
done
python3 $S sheet review/followup3/sheet_walk_side.png review/followup3/installed review/followup3/fixed $T walk0R,walk1R,walk2R,walk3R,walkH
python3 $S sheet review/followup3/sheet_walk_quarter.png review/followup3/installed review/followup3/fixed $T walk1Q,walk3Q,standR
python3 $S sheet review/followup3/sheet_run.png review/followup3/installed review/followup3/fixed $T run1R,run2R,run1Q
python3 $S sheet review/followup3/sheet_gestures.png review/followup3/installed review/followup3/fixed $T fid1R,fid2R,fid1Q,att1R,att2R,att1Q,hit1R,hit1Q
python3 $S sheet review/followup3/sheet_head_profile.png review/followup3/installed review/followup3/fixed $T standH,walk1H,walk3H,run1H
