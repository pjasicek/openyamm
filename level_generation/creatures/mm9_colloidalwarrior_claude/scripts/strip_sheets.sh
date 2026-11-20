#!/bin/bash
# strip sheets per tier (project folder). Args: tiers (a b c)
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
for t in "$@"; do
$G scripts/sheet.py review/sheet_strips_${t}_1.png 6 260 $(for c in Standing Walking Running Fidget Fidget2 Taunt; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
$G scripts/sheet.py review/sheet_strips_${t}_2.png 6 260 $(for c in AttackMelee AttackMelee2 AttackRanged Hit Hit2 Death; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
$G scripts/sheet.py review/sheet_strips_${t}_3.png 6 260 $(for c in Death2 Dead Backpedal BackpedalRun; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
done
