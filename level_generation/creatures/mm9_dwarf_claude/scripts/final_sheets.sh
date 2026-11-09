#!/usr/bin/env bash
# Viewer-shot sheets. Project folder. Heavy: one Chrome at a time per call.
set -uo pipefail
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
U=http://127.0.0.1:8912/level_generation/creatures/mm9_dwarf_claude/review/viewer/
V=../mm8_m424_claude/scripts/viewer_shots.mjs
mkdir -p review/final review/close
for t in a b c; do
  node $V "$U?model=dwarf_$t" $PWD/review/final t${t}_q:Standing:0.5:quarter:body t${t}_f:Standing:0.5:front:body t${t}_b:Standing:0.5:back:body t${t}_r:Standing:0.5:right:body t${t}_w:Walking:0.3:quarter:body t${t}_h:Standing:0.5:front:body:-0.4,1.15,0.55:0,1.12,0 t${t}_hf:Standing:0.5:front:body:0,1.12,0.7:0,1.12,0 t${t}_hb:Standing:0.5:front:body:0.3,1.2,-0.7:0,1.12,0 | tail -1
done
python3 scripts/sheet.py review/sheet_tiers.png 8 300 review/final/ta_*.png review/final/tb_*.png review/final/tc_*.png
# close-ups: knees, groin, armpits, elbows, neck, mouth, framed on the joint, crouch and death poses; every tier
SP() { $G scripts/close_specs.py export/mm9_dwarf.glb "$@" 2>/dev/null | tr '\n' ' '; }
for t in a b c; do
  S=""
  for cs in AttackMelee:0.6 Death:1.25 Dead:0.5 Running:0.17; do
    c=${cs%%:*}
    S+=" $(SP ${t}${c}_ $cs "Bip01 L Calf:0.8,0.1,-0.6:0.55" "Bip01 R Calf:-0.6,0.1,0.8:0.55" "Bip01 R Thigh:0.0,-0.3,1:0.7" "Bip01 R UpperArm:-1,-0.5,0.3:0.55" "Bip01 L UpperArm:1,-0.5,0.3:0.55" "Bip01 R Forearm:-0.5,0.5,1:0.5" "Bip01 Head:0.8,0.0,0.6:0.5" "Bip01 Neck:-0.5,0.3,1:0.5")"
  done
  echo $S | tr ' ' '\n' > work/spc.txt; split -l 16 -d work/spc.txt work/spc_
  for f in work/spc_0*; do node $V "$U?model=dwarf_$t" $PWD/review/close $(cat $f) | tail -1; done
  rm -f work/spc_00 work/spc_01 work/spc_02
done
for t in a b c; do
  python3 scripts/sheet.py review/sheet_closeups_$t.png 8 300 $(for c in AttackMelee Death Dead Running; do for k in 0 1 2 3 4 5 6 7; do echo review/close/${t}${c}_$k.png; done; done)
done
# hands and axe
S=""
for cs in Standing:0.5 AttackMelee:0.4 AttackRanged:0.45 Death:1.25; do c=${cs%%:*}; S+=" $(SP g${c}_ $cs "Bip01 R Hand:-1,-0.3,0.6:0.42" "Bip01 R Hand:0.3,-0.8,1:0.42" "Bip01 L Hand:1,-0.3,0.6:0.42" "Bip01 L Hand:-0.3,-0.8,1:0.42")"; done
node $V "$U?model=dwarf_a" $PWD/review/close $S | tail -1
python3 scripts/sheet.py review/sheet_hands.png 4 400 $(for c in Standing AttackMelee AttackRanged Death; do for k in 0 1 2 3; do echo review/close/g${c}_$k.png; done; done)
