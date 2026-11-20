#!/bin/bash
# Viewer-lit arm and torso shots (job 8, user review 2026-11-04: forearm sleeve holes, bodice hem spikes, chest holes), both tiers.
# Usage (repo root): level_generation/creatures/mm9_peasantf4_claude/scripts/arm_shots_pf4.sh <rev> [clip:sec]
set -euo pipefail
P=level_generation/creatures/mm9_peasantf4_claude; R=$1; CS=${2:-Standing:0}; O=$P/review/arms/$R${2:+_${CS%%:*}}; mkdir -p $O
URL=http://127.0.0.1:8912/$P/review/viewer/
C=${CS%%:*}; S=${CS##*:}
# viewer frame: Y up, the model faces +Z, her left arm at +X
SPEC="armsF:$C:$S:front:body:0,1.10,1.25:0,1.02,0 armsB:$C:$S:back:body:0,1.10,-1.25:0,1.02,0
armQL:$C:$S:quarter:body:0.85,1.15,0.75:0.2,1.0,0 armQR:$C:$S:quarter:body:-0.85,1.15,0.75:-0.2,1.0,0
armBL:$C:$S:back:body:0.75,1.15,-0.75:0.2,1.0,0 armBR:$C:$S:back:body:-0.75,1.15,-0.75:-0.2,1.0,0
lowL:$C:$S:quarter:body:0.55,0.70,0.65:0.2,1.05,0 lowR:$C:$S:quarter:body:-0.55,0.70,0.65:-0.2,1.05,0
elbL:$C:$S:left:body:0.62,1.08,0.10:0.22,1.02,0 elbR:$C:$S:right:body:-0.62,1.08,0.10:-0.22,1.02,0
torsoF:$C:$S:front:body:0,1.20,0.62:0,1.12,0 torsoQ:$C:$S:quarter:body:-0.42,1.18,0.48:0,1.10,0
hemB:$C:$S:back:body:0,1.05,-0.62:0,1.00,0"
for t in a b; do
  SHA=$(python3 -c "import json;m=json.load(open('$P/review/viewer/manifest.json'));print(next(x['sha256'] for x in m['models'] if x['id']=='pf4_$t'))")
  H=$(python3 -c "import json,urllib.parse;print(urllib.parse.quote(json.dumps({'clip':'$C','model_sha256':'$SHA'})))")
  specs=(); for s in $SPEC; do specs+=("${t}_${s}"); done
  MODEL_SHA=$SHA timeout 600 node $P/scripts/viewer_shots_pf4.mjs "$URL#$H" $O "${specs[@]}" | tail -1
done
