#!/bin/bash
# tier, head, hand and close-up sheets. Project folder.
G=$PWD/../claude_shared/gltf_venv/bin/python
for t in a b c; do scripts/shots.sh $t review/final t${t}_q:Standing:0.5:quarter:body t${t}_f:Standing:0.5:front:body t${t}_l:Standing:0.5:left:body t${t}_b:Standing:0.5:back:body t${t}_w:Walking:0.3:quarter:body t${t}_a:AttackMelee:0.55:quarter:body; done
SP() { REF="$R" $G -W ignore scripts/close_specs.py export/mm9_nobleman.glb "$@" 2>/dev/null | tr '\n' ' '; }
R="Bip01 Head"; S="$(SP h_ Standing:0.5 'Bip01 Head:0,0.3,1:0.55' 'Bip01 Head:-1,0.3,0.6:0.55' 'Bip01 Head:1,0.3,0.6:0.55' 'Bip01 Head:0,0.4,-1:0.55' 'Bip01 Head:0,1,0.2:0.55')"
for t in a b c; do scripts/shots.sh $t review/close $(echo $S | sed "s/h_/h${t}_/g"); done
R="Bip01 Spine2"; S="$(SP g_ Standing:0.5 'Bip01 R Hand:-1,0.3,0.6:0.4' 'Bip01 L Hand:1,0.3,0.6:0.4') $(SP g2_ AttackMelee:0.55 'Bip01 R Hand:-0.4,0.8,1:0.4' 'Bip01 L Hand:1,0.3,0.6:0.4') $(SP g3_ Cower:1.2 'Bip01 R Hand:-0.4,0.8,1:0.4' 'Bip01 L Hand:0.4,0.8,1:0.4') $(SP g4_ Fidget:2.6 'Bip01 R Hand:0,0.5,1:0.5' 'Bip01 L Hand:1,0.2,1:0.5')"
scripts/shots.sh a review/close $S
scripts/close.sh a; scripts/close.sh b; scripts/close.sh c
for t in a b c; do scripts/shots.sh $t review/final c${t}_0:Standing:0.5:quarter:body c${t}_1:Walking:0.3:quarter:body c${t}_2:Running:0.25:quarter:body c${t}_3:AttackMelee:0.55:quarter:body c${t}_4:AttackMelee2:0.8:quarter:body c${t}_5:Hit:0.3:quarter:body c${t}_6:Death:1.0:quarter:body c${t}_7:Cower:1.0:quarter:body; done
echo DONE2
