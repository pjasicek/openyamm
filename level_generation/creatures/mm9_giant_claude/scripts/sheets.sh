#!/bin/bash
# Viewer shots and review sheets for the final build (project folder). One Chrome at a time (vsr.sh).
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
mkdir -p review/shots review/strips_a review/strips_b
for t in a b; do
  scripts/vsr.sh gi_$t review/shots s${t}_front:Standing:0:front:body:0,1.3,5.8:0,1.3,0.25 s${t}_back:Standing:0:front:body:0,1.3,-5.4:0,1.3,0.25 s${t}_quarter:Standing:0:front:body:-3,1.5,4.8:0,1.3,0.25 \
    s${t}_fh:Standing:0:front:body:0,2.2,1.6:0,2.2,0.2 s${t}_qh:Standing:0:front:body:-0.9,2.2,1.4:0,2.2,0.2 s${t}_sh:Standing:0:front:body:-1.6,2.2,0.1:0,2.2,0.1 s${t}_bh:Standing:0:front:body:0,2.2,-1.4:0,2.2,0.0 \
    s${t}_tex_chest:Standing:0:front:body:0,1.75,1.1:0,1.75,0.2 s${t}_tex_legs:Standing:0:front:body:0,0.55,1.4:0,0.55,0.1 s${t}_tex_back:Standing:0:front:body:0,1.5,-1.3:0,1.5,0 s${t}_tex_mallet:Standing:0:front:body:1.1,1.6,1.2:0.9,1.25,0.3 \
    s${t}_fist:Standing:0:front:body:-0.4,1.35,1.0:-0.25,1.1,0.4 s${t}_fist2:AttackMelee:0.3:front:body:-0.6,2.3,1.2:0,2.0,0.2
  scripts/vsr.sh gi_$t review/strips_$t $($G scripts/strips.py export/mm9_giant.glb 6 2>/dev/null | sed 's/-2.6,2.0,4.0:0,1.1,0/-3.4,2.2,5.0:0,1.2,0/')
  scripts/closeups.sh gi_$t c$t
done
for t in a b; do
  $G scripts/sheet.py review/sheet_strips_${t}_1.png 6 240 $(for c in Standing Walking Running Fidget Fidget2 Taunt Aware AttackMelee; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
  $G scripts/sheet.py review/sheet_strips_${t}_2.png 6 240 $(for c in AttackMelee2 AttackMelee3 AttackRanged Hit Hit2 Death Death2 Dead; do for k in 00 01 02 03 04 05; do echo review/strips_$t/st_${c}_$k.png; done; done)
  $G scripts/sheet.py review/sheet_closeups_${t}.png 6 300 $(ls review/shots | grep "^c$t" | sed 's#^#review/shots/#')
done
echo SHEETSDONE
