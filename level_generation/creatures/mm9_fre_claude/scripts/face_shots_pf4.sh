#!/bin/bash
# Viewer-lit face pre-screen shots (the three.js review viewer, what the user sees) for both tiers, plus MM9 F4 renders at matching angles
# (Blender, studio light, bind pose) and one sheet per run. VARIANTS_BRIEF face lessons: front close-up, 3/4, true profiles, low 3/4 from
# below, party view (and its 128 px simulation), Talk mid-sentence, ear / hood-edge close-ups, under the jaw.
# Usage (repo root): level_generation/creatures/mm9_peasantf4_claude/scripts/face_shots_pf4.sh <rev>
set -euo pipefail
P=level_generation/creatures/mm9_peasantf4_claude; R=$1; O=$P/review/faces/$R; mkdir -p $O
URL=http://127.0.0.1:8912/$P/review/viewer/
T=0,1.585,0.03
S="front:Standing:0:front:head:0,1.60,0.42:$T q34:Standing:0:quarter:head:-0.27,1.62,0.32:$T profL:Standing:0:left:head:0.42,1.59,0.03:$T
profR:Standing:0:right:head:-0.42,1.59,0.03:$T low34:Standing:0:quarter:head:-0.22,1.40,0.30:0,1.56,0.03
party:Standing:0:front:body:0.18,2.02,1.02:0,1.50,0.03 talk:Talk:1.4:front:head:-0.10,1.60,0.40:$T
earL:Standing:0:left:head:0.26,1.60,0.10:0.06,1.58,0.0 earR:Standing:0:right:head:-0.26,1.60,0.10:-0.06,1.58,0.0
jaw:Standing:0:front:head:0.0,1.36,0.30:0,1.52,0.03"
for t in a b; do
  SHA=$(python3 -c "import json;m=json.load(open('$P/review/viewer/manifest.json'));print(next(x['sha256'] for x in m['models'] if x['id']=='pf4_$t'))")
  H=$(python3 -c "import json,urllib.parse;print(urllib.parse.quote(json.dumps({'clip':'Standing','model_sha256':'$SHA'})))")
  specs=(); for s in $S; do n=${s%%:*}; specs+=("${t}_${s}"); done
  MODEL_SHA=$SHA timeout 600 node $P/scripts/viewer_shots_pf4.mjs "$URL#$H" $O "${specs[@]}" | tail -1
done
