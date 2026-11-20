#!/bin/bash
for t in ${1:-a b c}; do
python3 scripts/sheet.py review/sheet_strips_${t}_1.png 6 300 $(for c in Standing Walking Running Fidget Fidget2 Taunt AttackMelee AttackMelee2; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
python3 scripts/sheet.py review/sheet_strips_${t}_2.png 6 300 $(for c in AttackMelee3 AttackRanged Hit Hit2 Death Death2 Dead; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
done
