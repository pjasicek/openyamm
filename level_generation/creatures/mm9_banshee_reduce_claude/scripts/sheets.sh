#!/bin/bash
# Comparison sheets (installed vs reduced) from viewer shots, one shot script at a time and at most two on the machine.
# Run from anywhere; output review/sheets/.
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm9_banshee_reduce_claude
wait_slot() { while [ "$(pgrep -x node -a | grep -c viewer_shots.mjs)" -ge 2 ]; do sleep 5; done; }
FACE="f1:Standing:0:Xhead:0:-3:0.62 f2:Standing:0:Xhead:40:0:0.62 f3:Standing:0:Xhead:90:0:0.62 f4:Standing:0:Xhead:35:-25:0.6 f5:Standing:0.4:Xhead:10:12:2.6 f6:AttackMelee:0.7:Xjaw:10:-20:0.5"
BODY="b1:Standing:0.4:XCENTER:0:5:3.4 b2:Standing:0.4:XCENTER:35:5:3.4 b3:Standing:0.4:XCENTER:180:5:3.4 b4:Walking:0.3:XCENTER:35:10:3.4 b5:Walking:0.6:XCENTER:160:10:3.4 b6:AttackMelee:0.7:XCENTER:35:5:3.4 b7:Fidget2:1.87:XCENTER:200:10:3.4 b8:Death:1.5:XCENTER:40:20:3.4"
DETAIL="d1:Standing:0.4:XCENTER:0:0:1.3 d2:Standing:0.4:XCENTER:180:0:1.4 d3:Standing:0.4:Xspine2:20:5:0.7 d4:AttackMelee:0.7:Zarm01:150:5:0.7 d5:AttackMelee:0.27:Zarmpiv01:-60:10:0.6 d6:Fidget2:1.47:Zarm:60:10:0.6 d7:Walking:0.3:XCENTER:150:15:1.6 d8:Fidget2:1.87:XCENTER:200:10:1.6 d9:Death:0.5:XCENTER:40:20:1.6 d10:Dead:0.5:XCENTER:-140:35:1.3"
for t in ${TIERS:-a b c}; do
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/face_$t.png $t reduced $FACE 2>&1 | tail -1
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/body_$t.png $t reduced $BODY 2>&1 | tail -1
done
for t in ${DETAIL_TIERS:-a c}; do
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/detail_$t.png $t reduced $DETAIL 2>&1 | tail -1
done
