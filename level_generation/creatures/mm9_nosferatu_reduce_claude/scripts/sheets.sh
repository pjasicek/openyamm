#!/bin/bash
# Comparison sheets (installed vs reduced) from viewer shots, at most two shot scripts on the machine. Output review/sheets/.
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm9_nosferatu_reduce_claude
wait_slot() { while [ "$(pgrep -x node -a | grep -c viewer_shots.mjs)" -ge 2 ]; do sleep 5; done; }
mkdir -p $P/review/sheets
H=Bip01_Head@0.12
FACE="f1:Standing:0:$H:0:-3:0.62 f2:Standing:0:$H:-40:0:0.62 f3:Standing:0:$H:-90:0:0.62 f4:Standing:0:$H:-35:-25:0.6 f5:Standing:0.4:$H:10:12:2.6 f6:AttackMelee:0.5:$H:20:-5:0.6"
BODY="b1:Standing:0.4:Bip01:0:5:3.4 b2:Standing:0.4:Bip01:35:5:3.4 b3:Standing:0.4:Bip01:180:5:3.4 b4:Walking:0.3:Bip01:35:10:3.4 b5:Walking:0.6:Bip01:160:10:3.4 b6:AttackRanged:0.5:Bip01:35:5:3.4 b7:Fidget:0.7:Bip01:30:10:3.4 b8:Death:1.5:Bip01:40:20:3.4"
DETAIL="d1:Standing:0.4:Bip01_Spine2:0:0:1.0 d2:Standing:0.4:Bip01_Spine2:180:0:1.0 d3:Standing:0.4:Bip01:0:0:1.5 d4:Standing:0.4:Bip01:150:5:1.5 d5:Fidget:0.7:Bip01_L_Hand:20:10:0.6 d6:AttackRanged:0.2:Bip01_R_Hand:60:10:0.7 d7:Running:0.3:Bip01:40:15:1.8 d8:Hit2:0.3:Bip01_Spine2:30:10:1.0 d9:Death2:1.0:Bip01:40:25:1.8 d10:Dead:0.5:Bip01:-140:35:1.6"
for t in ${TIERS:-a b c}; do
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/face_$t.png $t reduced $FACE 2>&1 | tail -1
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/body_$t.png $t reduced $BODY 2>&1 | tail -1
done
for t in ${DETAIL_TIERS:-b c}; do
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/detail_$t.png $t reduced $DETAIL 2>&1 | tail -1
done
