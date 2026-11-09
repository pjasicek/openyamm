#!/bin/bash
# Viewer back views of the forearms and the back hem (job 8 follow-up, user 2026-11-04 13_back_elbows_r40.png), both tiers.
# Usage (repo root): level_generation/creatures/mm9_peasantf4_claude/scripts/back_shots_pf4.sh <rev> [clip:sec ...]
set -euo pipefail
P=level_generation/creatures/mm9_peasantf4_claude; R=$1; shift; CLIPS=${@:-Standing:0}
URL=http://127.0.0.1:8912/$P/review/viewer/
for CS in $CLIPS; do
  C=${CS%%:*}; S=${CS##*:}; O=$P/review/back/$R/${C}_$S; mkdir -p $O
  # viewer frame: Y up, the model faces +Z (back = -Z), her left arm at +X
  SPEC="back:$C:$S:back:body:0,1.00,-1.05:0,1.02,0 backlow:$C:$S:back:body:0,0.80,-0.85:0,1.05,0
  elbBL:$C:$S:back:body:0.32,0.92,-0.50:0.22,1.06,0 elbBR:$C:$S:back:body:-0.32,0.92,-0.50:-0.22,1.06,0
  q34BL:$C:$S:back:body:0.65,1.00,-0.60:0.2,1.03,0 q34BR:$C:$S:back:body:-0.65,1.00,-0.60:-0.2,1.03,0
  hemBL:$C:$S:back:body:0.25,0.95,-0.55:0.12,1.00,0 hemBR:$C:$S:back:body:-0.25,0.95,-0.55:-0.12,1.00,0"
  for t in a b; do
    SHA=$(python3 -c "import json;m=json.load(open('$P/review/viewer/manifest.json'));print(next(x['sha256'] for x in m['models'] if x['id']=='pf4_$t'))")
    H=$(python3 -c "import json,urllib.parse;print(urllib.parse.quote(json.dumps({'clip':'$C','model_sha256':'$SHA'})))")
    specs=(); for s in $SPEC; do specs+=("${t}_${s}"); done
    MODEL_SHA=$SHA timeout 600 node $P/scripts/viewer_shots_pf4.mjs "$URL#$H" $O "${specs[@]}" | tail -1
  done
done
