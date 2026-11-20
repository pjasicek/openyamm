#!/usr/bin/env bash
# Viewer-shot sheets (project folder): body views, head at full size, close-ups framed on the joints (crouch, death, corpse, run), hands.
set -uo pipefail
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
E=export/mm9_njam.glb
mkdir -p review/final review/close
scripts/shots.sh review/final q:Standing:0.5:quarter:body f:Standing:0.5:front:body b:Standing:0.5:back:body r:Standing:0.5:right:body \
  w:Walking:0.3:quarter:body run:Running:0.3:quarter:body | tail -1
python3 scripts/sheet.py review/sheet_body.png review/final/{q,f,b,r,w,run}.png
# head at full size: front, quarter, side, back, below; and in two clips
SP() { $G -W ignore scripts/close_specs.py $E "$@" 2>/dev/null | tr '\n' ' '; }
S="$(TOFF=0,0.075,0.02 SP hd_ Standing:0.5 'Bip01 Head:0,0.05,1:0.45' 'Bip01 Head:-0.7,0.05,0.7:0.45' 'Bip01 Head:-1,0.05,0:0.45' 'Bip01 Head:0,0.1,-1:0.45' 'Bip01 Head:0,-0.7,0.7:0.45' 'Bip01 Head:0.7,0.05,0.7:0.45')"
scripts/shots.sh review/close $S | tail -1
python3 scripts/sheet.py review/sheet_head_full.png review/close/hd_{0,1,2,3,4,5}.png
# close-ups framed on the joints, offsets in the body's rest frame (glTF: +z = the figure's front, -x = its right)
for cs in CowerLoop:0.5 Death:1.4 Dead:0.5 Running:0.3 Kick:0.9; do
  c=${cs%%:*}
  S="$(SP ${c}_ $cs 'Bip01 L Calf:0.8,0.1,0.6:0.6' 'Bip01 R Calf:-0.8,0.1,0.6:0.6' 'Bip01 Spine:0,-0.4,1:0.7' 'Bip01 R UpperArm:-1,-0.4,0.3:0.55' 'Bip01 L UpperArm:1,-0.4,0.3:0.55' 'Bip01 R Forearm:-0.6,0.3,0.8:0.5' 'Bip01 L Forearm:0.6,0.3,0.8:0.5')"
  S+=" $(TOFF=0,0.04,0.03 SP ${c}_m $cs 'Bip01 Head:0.3,-0.2,1:0.4')"
  scripts/shots.sh review/close $S | tail -1
  python3 scripts/sheet.py review/sheet_close_$c.png review/close/${c}_{0,1,2,3,4,5,6}.png review/close/${c}_m0.png
done
# hands
S=""
for cs in Standing:0.5 AttackRanged:0.866 Cast:1.466 Death:1.4; do c=${cs%%:*}; S+=" $(SP g${c}_ $cs 'Bip01 R Hand:-1,-0.3,0.6:0.42' 'Bip01 L Hand:1,-0.3,0.6:0.42')"; done
scripts/shots.sh review/close $S | tail -1
python3 scripts/sheet.py review/sheet_hands.png $(for c in Standing AttackRanged Cast Death; do echo review/close/g${c}_0.png review/close/g${c}_1.png; done)
echo SHEETS done
