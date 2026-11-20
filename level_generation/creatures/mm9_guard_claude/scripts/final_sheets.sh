#!/usr/bin/env bash
# Viewer-shot sheets. Project folder. Usage: scripts/final_sheets.sh
set -euo pipefail
PY=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
U=http://127.0.0.1:8912/level_generation/creatures/mm9_guard_claude/review/viewer/
V=../mm8_m424_claude/scripts/viewer_shots.mjs
mkdir -p review/final
for t in a b c; do
  node $V "$U?model=guard_$t" review/final t${t}_q:Standing:0.5:quarter:body t${t}_f:Standing:0.5:front:body t${t}_b:Standing:0.5:back:body t${t}_r:Standing:0.5:right:body t${t}_w:Walking:0.3:quarter:body t${t}_h:Standing:0.5:front:head >/dev/null
done
python3 scripts/shots_sheet.py review/sheet_tiers.png 6 480 review/final/ta_*.png review/final/tb_*.png review/final/tc_*.png | tail -1
rm -f /tmp/claude-1000/s4.txt
G=review/viewer/guard_a.glb
for cs in Cower:0.9 Cower:1.5 Death:1.0 Dead:0.5 Running:0.1 AttackMelee:0.5; do
  $PY scripts/close_specs.py $G "${cs%%:*}${cs##*.}_" $cs "Bip01 R Calf:-0.5,0.2,1:0.55" "Bip01 L Calf:0.6,0.2,1:0.55" "Bip01 R Thigh:-0.3,-0.3,1:0.7" "Bip01 R UpperArm:-1,-0.6,0.6:0.55" "Bip01 L UpperArm:1,-0.6,0.5:0.55" "Bip01 R Forearm:-1,0.1,0.5:0.5" "Bip01 Neck:-0.5,0.1,1:0.5" "Bip01 Head:-0.2,0.1,1:0.42" 2>/dev/null >> /tmp/claude-1000/s4.txt
done
for t in a c; do
  split -l 16 -d /tmp/claude-1000/s4.txt /tmp/claude-1000/s4p
  for f in /tmp/claude-1000/s4p*; do node $V "$U?model=guard_$t" review/final/c$t $(cat $f) >/dev/null; done
  rm -f /tmp/claude-1000/s4p*
  python3 scripts/shots_sheet.py review/sheet_closeups_$t.png 8 420 review/final/c$t/Cower9_*.png review/final/c$t/Cower5_*.png review/final/c$t/Death0_*.png review/final/c$t/Dead5_*.png review/final/c$t/Running1_*.png review/final/c$t/AttackMelee5_*.png | tail -1
done
