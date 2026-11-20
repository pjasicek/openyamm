#!/bin/bash
# frame strips of every clip for one tier, viewer shots: scripts/strips.sh <a|b|c>
. scripts/env.sh
t=$1
S=$($PYG -W ignore scripts/strips.py export/mm9_nosferatu.glb 7 "" s$t 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
scripts/vs2.sh nos_$t review/shots $S
python3 scripts/strip_sheet.py s$t review/strip_$t.png 240 7 Standing Walking Running Backpedal BackpedalRun Fidget Fidget2 Taunt AttackMelee AttackRanged ResurrectSpell Hit Hit2 Death Death2 Resurrect Dead
