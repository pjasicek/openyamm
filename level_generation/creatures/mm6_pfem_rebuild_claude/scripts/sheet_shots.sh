#!/usr/bin/env bash
# Before/after viewer shots at identical cameras, every tier (project folder): scripts/sheet_shots.sh -> review/shots_before, review/shots_after,
# review/sheet_before_after.png (body rows) and review/sheet_before_after_close.png (face and hands)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; repo="$(cd -- "$here/../../.." && pwd)"
G=$here/../claude_shared/gltf_venv/bin/python; S=$repo/level_generation/creatures/claude_shared/texpass_viewer_shots.py
SPECS=("stand:Standing:0:front:body" "standq:Standing:0:quarter:body" "back:Standing:0:back:body" "walk:Walking:0.3:quarter:body"
       "attack:Attack:0.48:front:body" "hit:Hit:0.3:quarter:body" "dead:Dead:0.5:quarter:body"
       "face:Standing:0:front:head:0,1.53,0.42:0,1.53,0" "faceq:Standing:0:front:head:0.3,1.53,0.3:0,1.53,0"
       "handL:Standing:1.2:front:body:0.6,0.9,0.4:0.25,0.85,0" "handR:Standing:1.2:front:body:-0.6,0.9,0.4:-0.25,0.85,0")
mkdir -p review/shots_before review/shots_after
$G -W ignore scripts/viewer_manifest.py before sheet > /dev/null
(cd "$repo" && python3 $S shots $here $here/review/shots_before pfem_a_before,pfem_b_before,pfem_c_before "${SPECS[@]}" | tail -3)
$G -W ignore scripts/viewer_manifest.py rebuild ${1:-final} > /dev/null
(cd "$repo" && python3 $S shots $here $here/review/shots_after pfem_a_rebuild,pfem_b_rebuild,pfem_c_rebuild "${SPECS[@]}" | tail -3)
for t in a b c; do for f in review/shots_before/pfem_${t}_before_*.png; do n=${f##*_before_}; cp "$f" review/shots_before/pfem_${t}_$n; done
  for f in review/shots_after/pfem_${t}_rebuild_*.png; do n=${f##*_rebuild_}; cp "$f" review/shots_after/pfem_${t}_$n; done; done
python3 $S sheet review/sheet_before_after.png review/shots_before review/shots_after pfem_a,pfem_b,pfem_c stand,standq,back,walk,attack,hit,dead
python3 $S sheet review/sheet_before_after_close.png review/shots_before review/shots_after pfem_a,pfem_b,pfem_c face,faceq,handL,handR
