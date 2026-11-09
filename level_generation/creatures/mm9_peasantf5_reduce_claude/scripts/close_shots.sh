#!/bin/bash
# Close viewer shots installed vs reduced (PeasantF5): arms, skirt front/back, Running skirt, feet, Talk arms, shoulders from
# behind, Hit; hands and wrists (bracelet over the MPFB junction) from close_specs.py on the hand joints; coif from behind above.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_peasantf5.glb
H=$($G -W ignore ../mm9_peasantf5_claude/scripts/close_specs.py $g h Standing:0.5 "FHP L Hand:1,0.2,0.3:0.28" "FHP R Hand:-1,0.2,0.3:0.28" "FHP R Hand:0,0.1,1:0.28" "FHP L Forearm:0.6,0.3,1:0.35" "FHP R Hand:-0.3,0.2,1:0.22" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
T=$($G -W ignore ../mm9_peasantf5_claude/scripts/close_specs.py $g t Talk:1.5 "FHP R Hand:0.2,0.2,1:0.3" "FHP L Hand:-0.2,0.2,1:0.3" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c11:Standing:0.5:front:body:0.25,1.95,-0.55:0.0,1.62,-0.05"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf5_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C $H $T 2>&1 | tail -1
  cd $P
done
