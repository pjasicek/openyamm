#!/usr/bin/env bash
# Neck and mouth close-ups where the collapse gate counts folds (run 2): Sleep, Hit2, AttackMelee3, Cower standing poses from the front and below, Death/Dead from above. Every tier. Project folder.
set -uo pipefail
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
U=http://127.0.0.1:8912/level_generation/creatures/mm9_dookmilitia_claude/review/viewer/
V=../mm8_m424_claude/scripts/viewer_shots.mjs
mkdir -p review/close
SP() { $G scripts/close_specs.py export/mm9_dookmilitia.glb "$@" 2>/dev/null | tr '\n' ' '; }
for t in a b c; do
  S="$(SP n${t}Sleep_ Sleep:0.8 'Bip01 Head:0.1,-0.6,1:0.42' 'Bip01 Neck:0.8,-0.3,0.5:0.42')"
  S+=" $(SP n${t}Hit2_ Hit2:0.5 'Bip01 Head:0.1,-0.6,1:0.42' 'Bip01 Neck:-0.8,-0.3,0.5:0.42')"
  S+=" $(SP n${t}AttackMelee3_ AttackMelee3:0.33 'Bip01 Head:0.1,-0.6,1:0.42' 'Bip01 L Clavicle:0.6,0.2,1:0.5')"
  S+=" $(SP n${t}Cower_ Cower:1.2 'Bip01 Head:0.1,-0.8,1:0.42' 'Bip01 Neck:-0.8,-0.5,0.5:0.42')"
  S+=" $(SP n${t}Death_ Death:1.25 'Bip01 Head:0.3,1,0.3:0.42' 'Bip01 Neck:-0.4,1,0.4:0.42')"
  S+=" $(SP n${t}Dead_ Dead:0.5 'Bip01 Head:0.3,1,0.3:0.42' 'Bip01 L UpperArm:0.6,1,0.2:0.5')"
  node $V "$U?model=dook_$t" $PWD/review/close $S | tail -1
done
python3 scripts/sheet.py review/sheet_neck_mouth.png 6 340 $(for t in a b c; do for c in Sleep Hit2 AttackMelee3 Cower Death Dead; do echo review/close/n${t}${c}_0.png; done; for c in Sleep Hit2 AttackMelee3 Cower Death Dead; do echo review/close/n${t}${c}_1.png; done; done)
