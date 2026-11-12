#!/usr/bin/env bash
# Before/after viewer shots at identical cameras, every tier (project folder): scripts/sheet_shots.sh [rev] [after-only] -> review/shots_before,
# review/shots_after, review/sheet_before_after.png (body rows) and review/sheet_before_after_close.png (face and hands). The before model is
# 3.4 % shorter in model units (1.70 m against 1.76 m), so its close-up cameras are scaled by 0.966.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"; repo="$(cd -- "$here/../../.." && pwd)"
G=$here/../claude_shared/gltf_venv/bin/python; S=$repo/level_generation/creatures/claude_shared/texpass_viewer_shots.py
BODY=("stand:Standing:0:front:body" "standq:Standing:0:quarter:body" "back:Standing:0:back:body" "walk:Walk2:0.3:quarter:body"
      "jog:Jog:0.3:left:body" "attackup:Attack:0.25:quarter:body" "attack:Attack:0.42:front:body" "hit:Hit:0.3:quarter:body" "dead:Dead:0.5:quarter:body")
close() { local k=$1; python3 - "$k" <<'PY'
import sys; k=float(sys.argv[1])
c=lambda *v: ','.join(f'{x*k:.3f}' for x in v)
for n,cam,tgt in (('face',(0,1.60,0.45),(0,1.60,0)),('faceq',(0.32,1.60,0.32),(0,1.60,0)),('handL',(0.85,0.95,0.45),(0.45,0.92,0)),('handR',(-0.85,0.95,0.45),(-0.45,0.92,0))):
    print(f'{n}:Standing:0.5:front:body:{c(*cam)}:{c(*tgt)}')
PY
}
mapfile -t CA < <(close 1.0); mapfile -t CB < <(close 0.966)
mkdir -p review/shots_before review/shots_after
$G -W ignore scripts/viewer_manifest.py rebuild ${1:-final} > /dev/null
(cd "$repo" && python3 $S shots $here $here/review/shots_after mer1_a_rebuild,mer1_b_rebuild,mer1_c_rebuild "${BODY[@]}" "${CA[@]}" | tail -3)
if [[ -z "${2:-}" ]]; then
$G -W ignore scripts/viewer_manifest.py before sheet > /dev/null
(cd "$repo" && python3 $S shots $here $here/review/shots_before mer1_a_before,mer1_b_before,mer1_c_before "${BODY[@]}" "${CB[@]}" | tail -3)
$G -W ignore scripts/viewer_manifest.py rebuild ${1:-final} > /dev/null
fi
for t in a b c; do for f in review/shots_before/mer1_${t}_before_*.png; do [[ -e $f ]] || continue; n=${f##*_before_}; cp "$f" review/shots_before/mer1_${t}_$n; done
  for f in review/shots_after/mer1_${t}_rebuild_*.png; do n=${f##*_rebuild_}; cp "$f" review/shots_after/mer1_${t}_$n; done; done
python3 $S sheet review/sheet_before_after.png review/shots_before review/shots_after mer1_a,mer1_b,mer1_c stand,standq,back,walk,jog,attackup,attack,hit,dead
python3 $S sheet review/sheet_before_after_close.png review/shots_before review/shots_after mer1_a,mer1_b,mer1_c face,faceq,handL,handR
