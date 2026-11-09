#!/usr/bin/env bash
# Viewer-shot sheets. Project folder.
set -uo pipefail
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
U=http://127.0.0.1:8912/level_generation/creatures/mm9_clansoldier_claude/review/viewer/
V=../mm8_m424_claude/scripts/viewer_shots.mjs
mkdir -p review/final review/close
for t in a b c; do
  timeout 280 node $V "$U?model=clan_$t" $PWD/review/final t${t}_q:Standing:0.5:quarter:body t${t}_f:Standing:0.5:front:body t${t}_b:Standing:0.5:back:body t${t}_r:Standing:0.5:right:body t${t}_w:Walking:0.3:quarter:body t${t}_x:AttackMelee:0.32:quarter:body t${t}_y:AttackMelee2:0.35:quarter:body t${t}_h:Hit:0.3:quarter:body t${t}_d:Dead:0.5:quarter:body t${t}_k:Block:0.3:quarter:body | tail -1
done
python3 scripts/sheet.py review/sheet_tiers.png 5 300 review/final/ta_{q,f,b,r}.png review/final/tb_{q,f,b,r}.png review/final/tc_{q,f,b,r}.png
SP() { $G scripts/close_specs.py export/mm9_clansoldier.glb "$@" 2>/dev/null | tr '\n' ' '; }
for t in a b c; do
  S=""
  for cs in Cower:1.2 Death:1.25 Dead:0.5 Running:0.17; do
    c=${cs%%:*}
    S+=" $(SP ${t}${c}_ $cs "Bip01 L Calf:0.8,0.1,-0.6:0.6" "Bip01 R Calf:-0.6,0.1,0.8:0.6" "Bip01 R Thigh:0.0,-0.3,1:0.75" "Bip01 R UpperArm:-1,-0.5,0.3:0.55" "Bip01 L UpperArm:1,-0.5,0.3:0.55" "Bip01 R Forearm:-0.6,0.8,0.3:0.5" "Bip01 L Thigh:0.3,1,0.2:0.75" "Bip01 L Forearm:0.6,0.8,0.3:0.5")"
  done
  timeout 280 node $V "$U?model=clan_$t" $PWD/review/close $S | tail -1
  python3 scripts/sheet.py review/sheet_closeups_$t.png 8 300 $(for c in Cower Death Dead Running; do for k in 0 1 2 3 4 5 6 7; do echo review/close/${t}${c}_$k.png; done; done)
done
