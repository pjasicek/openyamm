#!/bin/bash
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
for t in a b c; do
$G scripts/sheet.py review/sheet_strips_${t}_1.png 6 240 $(for c in Standing Walking Running Fidget Fidget2 Taunt AttackMelee; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
$G scripts/sheet.py review/sheet_strips_${t}_2.png 6 240 $(for c in AttackMelee2 AttackRanged Hit Hit2 Death Death2 Dead; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
$G scripts/sheet.py review/sheet_strips_${t}_3.png 6 240 $(for c in WalkFidget Backpedal BackpedalRun JumpingDown LyingDown; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
$G scripts/sheet.py review/sheet_closeups_${t}.png 6 300 $(ls review/shots | grep "^c$t" | sed 's/.png//')
done
