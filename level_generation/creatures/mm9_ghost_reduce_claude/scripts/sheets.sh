#!/bin/bash
# Comparison sheets (installed vs reduced) from viewer shots (from mm9_banshee_reduce_claude), one shot script at a time and
# at most two on the machine. Usage: sheets.sh <reduced suffix>; output review/sheets/.
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm9_ghost_reduce_claude; RED=${1:-reduced}
wait_slot() { while [ "$(pgrep -x node -a | grep -c viewer_shots.mjs)" -ge 2 ]; do sleep 5; done; }
FACE="f1:Standing:0:Xhead:0:-3:0.62 f2:Standing:0:Xhead:40:0:0.62 f3:Standing:0:Xhead:90:0:0.62 f4:Standing:0:Xhead:35:-25:0.6 f5:Standing:0.4:Xhead:10:12:2.6 f6:Taunt:0.6:Xhead:20:0:0.7"
BODY="b1:Standing:0.4:XCENTER:0:5:3.0 b2:Standing:0.4:XCENTER:35:5:3.0 b3:Standing:0.4:XCENTER:180:5:3.0 b4:Walking:0.3:XCENTER:35:10:3.0 b5:Walking:0.6:XCENTER:160:10:3.0 b6:AttackMelee:0.4:XCENTER:35:5:3.0 b7:Fidget2:1.2:XCENTER:200:10:3.0 b8:Death:0.5:XCENTER:40:20:3.0"
DETAIL="d1:Standing:0.4:Xspine2:0:0:1.1 d2:Standing:0.4:Xspine2:180:0:1.1 d3:Standing:0.4:XCENTER:20:-10:1.2 d4:Standing:0.4:XCENTER:180:-10:1.2 d5:Fidget2:1.667:Zarmpiv:150:-5:0.6 d6:AttackMelee:0.3:Zarmpiv01:-40:0:0.7 d7:Fidget2:1.2:Zarm:60:0:0.6 d8:Walking:0.3:XCENTER:150:15:1.4 d9:Fidget:3.6:XCENTER:0:-20:1.6 d10:Standing:0.4:Zhand01:-30:10:0.4 d11:Standing:0.4:Zhand:30:10:0.4 d12:Walking:0.3:XCENTER:0:-55:1.4"
for t in ${TIERS:-a b c}; do
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/face_$t.png $t $RED $FACE 2>&1 | tail -1
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/body_$t.png $t $RED $BODY 2>&1 | tail -1
done
for t in ${DETAIL_TIERS:-b c}; do
  wait_slot; python3 $P/scripts/cshot.py $P/review/sheets/detail_$t.png $t $RED $DETAIL 2>&1 | tail -1
done
