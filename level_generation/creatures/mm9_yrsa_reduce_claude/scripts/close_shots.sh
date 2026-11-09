#!/bin/bash
# Close viewer shots installed vs reduced (Kira, Standing 0.5 unless named): c0 arms 3/4, c1 skirt front, c2 skirt back, c3 Running
# skirt, c4 feet, c5 Fidget arms, c6 shoulders/hair from behind, c7 Hit, c8 L hand outside, c9 R hand on the hip outside, c10 R hand
# front, c11 hair from behind above, c12 medallion, c13 belt + tasset, c14 L knee cop, c15 R pauldron lames, c16 braid front,
# c17 L wrist rim, c18 R wrist rim (AttackMelee), c19 seated thighs (Sit). Usage: scripts/close_shots.sh [models]
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.4:quarter:body"
C="$C c8:Standing:0.5:front:body:0.72,1.0,0.25:0.28,0.92,-0.08 c9:Standing:0.5:front:body:-0.66,1.16,0.42:-0.22,1.10,0.0 c10:Standing:0.5:front:body:-0.08,1.12,0.62:-0.22,1.10,0.0"
C="$C c11:Standing:0.5:front:body:0.25,1.95,-0.62:0.0,1.6,-0.1 c12:Standing:0.5:front:body:0.12,1.50,0.48:0.0,1.47,0.07 c13:Standing:0.5:front:body:0.18,1.12,0.62:0.0,1.08,0.12"
C="$C c14:Standing:0.5:front:body:0.42,0.62,0.48:0.16,0.48,0.05 c15:Standing:0.5:front:body:-0.62,1.62,0.32:-0.22,1.45,-0.03 c16:Standing:0.5:front:body:-0.32,1.58,0.52:-0.09,1.50,0.06"
C="$C c17:Standing:0.5:front:body:0.62,1.08,0.12:0.25,0.99,-0.07 c18:AttackMelee:0.3:front:body:-0.70,1.70,0.70:-0.378,1.557,0.309 c19:Sit:0.5:quarter:body"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_yrsa_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
