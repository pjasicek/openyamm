#!/bin/bash
# Strip sheets from review/strips (project folder): every clip, six frames per row, three sheets.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
sh() { out=$1; shift; $G scripts/sheet.py $out 6 260 $(for c in "$@"; do for k in 00 01 02 03 04 05; do echo review/strips/st_${c}_$k.png; done; done); }
sh review/sheet_strips_1.png Standing Walking Running Fidget Fidget2 Taunt Wipe
sh review/sheet_strips_2.png AttackMelee AttackMelee2 StepOn AttackRanged AttackRanged2 KickDoor Hit Hit2
sh review/sheet_strips_3.png Death Death2 Dead StartDie Fall Die AttackRangedOld AttackMeleeSave
