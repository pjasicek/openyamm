#!/bin/bash
# tier C sheets again on the final build. Project folder.
G=$PWD/../claude_shared/gltf_venv/bin/python
SP() { REF="$R" $G -W ignore scripts/close_specs.py export/mm9_nobleman.glb "$@" 2>/dev/null | tr '\n' ' '; }
scripts/shots.sh c review/final tc_q:Standing:0.5:quarter:body tc_f:Standing:0.5:front:body tc_l:Standing:0.5:left:body tc_b:Standing:0.5:back:body tc_w:Walking:0.3:quarter:body tc_a:AttackMelee:0.55:quarter:body
scripts/shots.sh c review/final cc_0:Standing:0.5:quarter:body cc_1:Walking:0.3:quarter:body cc_2:Running:0.25:quarter:body cc_3:AttackMelee:0.55:quarter:body cc_4:AttackMelee2:0.8:quarter:body cc_5:Hit:0.3:quarter:body cc_6:Death:1.0:quarter:body cc_7:Cower:1.0:quarter:body
R="Bip01 Head"; S="$(SP hc_ Standing:0.5 'Bip01 Head:0,0.3,1:0.55' 'Bip01 Head:-1,0.3,0.6:0.55' 'Bip01 Head:1,0.3,0.6:0.55' 'Bip01 Head:0,0.4,-1:0.55' 'Bip01 Head:0,1,0.2:0.55') $(SP vc_ Standing:0.5 'Bip01 Head:0,0.25,1:0.5' 'Bip01 Head:-0.8,0.25,0.8:0.5' 'Bip01 Head:-1,0.15,0:0.5' 'Bip01 Head:0.6,-1,0.7:0.5')"
scripts/shots.sh c review/close $S
R="Bip01 Spine2"; scripts/shots.sh c review/close $(SP yc_ Standing:0.5 'Bip01 Neck:0,-0.15,1:0.34' 'Bip01 Neck:-0.5,0.1,1:0.36')
scripts/close.sh c
python3 scripts/strips.py nb_c review/strips_c.png 6 --fresh
echo DONE3
