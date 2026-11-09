#!/bin/bash
# Reduction review shots from the three.js viewer (PeasantF4's viewer_shots_pf4.mjs, read only; one shot script at a time), installed
# and reduced, both tiers: face sheet (front close-up, 3/4, true profiles, low 3/4, party; face_shots_pf4.sh cameras), body
# (Standing front / 3-4 / back, Walking 3/4, Talk 3/4, Death 3/4), arms from behind (back_shots_pf4.sh cameras: back, low back,
# back 3/4 both sides, elbows from behind, hem) and arms from the front (arm_shots_pf4.sh 3/4 and low 3/4). Optional extra clip:sec for
# the back views. Usage (project folder): scripts/shots.sh [models] [clip:sec]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=level_generation/creatures/mm9_peasantf4_reduce_claude
URL=http://127.0.0.1:8912/$P/review/viewer/
T=0,1.585,0.03
CS=${2:-Standing:0}; C=${CS%%:*}; S=${CS##*:}
FACE="f0:Standing:0:front:head:0,1.60,0.42:$T f1:Standing:0:quarter:head:-0.27,1.62,0.32:$T f2:Standing:0:left:head:0.42,1.59,0.03:$T
f3:Standing:0:right:head:-0.42,1.59,0.03:$T f4:Standing:0:quarter:head:-0.22,1.40,0.30:0,1.56,0.03 f5:Standing:0:front:body:0.18,2.02,1.02:0,1.50,0.03"
BODY="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:back:body b3:Walking:0.45:quarter:body b4:Talk:1.4:quarter:body b5:Death:1.2:quarter:body"
BACK="k0:$C:$S:back:body:0,1.00,-1.05:0,1.02,0 k1:$C:$S:back:body:0,0.80,-0.85:0,1.05,0
k2:$C:$S:back:body:0.32,0.92,-0.50:0.22,1.06,0 k3:$C:$S:back:body:-0.32,0.92,-0.50:-0.22,1.06,0
k4:$C:$S:back:body:0.65,1.00,-0.60:0.2,1.03,0 k5:$C:$S:back:body:-0.65,1.00,-0.60:-0.2,1.03,0
k6:$C:$S:back:body:0.25,0.95,-0.55:0.12,1.00,0 k7:$C:$S:back:body:-0.25,0.95,-0.55:-0.12,1.00,0"
ARMS="a0:$C:$S:quarter:body:0.85,1.15,0.75:0.2,1.0,0 a1:$C:$S:quarter:body:-0.85,1.15,0.75:-0.2,1.0,0
a2:$C:$S:quarter:body:0.55,0.70,0.65:0.2,1.05,0 a3:$C:$S:quarter:body:-0.55,0.70,0.65:-0.2,1.05,0
a4:$C:$S:front:body:0,1.20,0.62:0,1.12,0 a5:$C:$S:quarter:body:-0.42,1.18,0.48:0,1.10,0"
if [[ -n "${2:-}" ]]; then ALL="$BACK $ARMS"; SUB=_${C}; else ALL="$FACE $BODY $BACK $ARMS"; SUB=; fi
cd /home/pjasicek/github/OpenYAMM
for m in ${1:-inst_a red_a inst_b red_b}; do
  SHA=$(python3 -c "import json;m=json.load(open('$P/review/viewer/manifest.json'));print(next(x['sha256'] for x in m['models'] if x['id']=='$m'))")
  H=$(python3 -c "import json,urllib.parse;print(urllib.parse.quote(json.dumps({'clip':'Standing','model_sha256':'$SHA'})))")
  MODEL_SHA=$SHA timeout 900 node level_generation/creatures/mm9_peasantf4_claude/scripts/viewer_shots_pf4.mjs "$URL#$H" $P/review/shots$SUB/$m $ALL 2>&1 | tail -1
done
