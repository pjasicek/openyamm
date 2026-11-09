#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude; . scripts/env.sh
scripts/sheets.sh 2>&1 | tail -1
for t in a b c; do S=$($G scripts/closeups.py export/mm9_troglodyte.glb 2>/dev/null | sed "s/j_/j${t}_/g"); TIER=trog_$t scripts/vshots.sh $S 2>&1 | tail -1; done
python3 - <<'PY'
import subprocess
names='kneeL_crouch kneeL_inner kneeR_death kneeL_run groin_crouch groin_rear groin_dead groin_walk armpitL_taunt armpitR_hit armpitR_attack armpitL_attack2 elbowL_attack elbowR_taunt elbowR_stand elbowL_dead neck_taunt neck_hit neck_back neck_dead mouth_taunt mouth_hit mouth_side mouth_closed mouth_dead tailroot_walk tailroot_death2 ankle_hit hand_taunt hand_claws'.split()
for t in 'abc':
    subprocess.run(['python3','scripts/sheet.py',f'review/sheet_closeups_{t}.png','6','330']+[f'j{t}_{n}:{n}' for n in names])
PY
scripts/strips.sh 2>&1 | tail -1
echo DELIVERDONE
