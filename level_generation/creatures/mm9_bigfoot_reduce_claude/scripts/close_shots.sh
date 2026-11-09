#!/bin/bash
# Close viewer shots installed vs reduced (Bigfoot): head from behind and the side, hands, feet, shoulders in AttackMelee,
# Death2 head/mane, Running hooves. Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="k0:Standing:0.5:rear:head k1:Standing:0.5:right:head k2:Standing:0.5:front:arms k3:Standing:0.5:front:feet k4:AttackMelee:0.3:rear:shoulders k5:Death2:0.8:quarter:head k6:Walking:0.4:right:feet k7:Fidget2:1.0:quarter:arms"
for m in ${1:-inst_a red_a inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_bigfoot_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
