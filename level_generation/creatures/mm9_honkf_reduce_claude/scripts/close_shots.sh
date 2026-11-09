#!/bin/bash
# Close viewer shots of the reduced regions, installed vs reduced: hands (Standing, AttackMelee), goose hat 3/4 above and
# from behind, the veil from behind, braids on the chest, the left cuff from below, hem and boots in Walking, Death. Usage: scripts/close_shots.sh [models]
# -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python
C=$($G -W ignore scripts/close_specs.py before/mm9_honkf.glb \
  "c0:Standing:0.5:Bip01 L Hand:1,0.2,0.6:0.45" "c1:Standing:0.5:Bip01 R Hand:-1,0.2,0.6:0.45" \
  "c2:AttackMelee:0.3:Bip01 R Hand:-0.4,0.3,1:0.5" "c3:Standing:0.5:Bip01 Head:0.6,0.5,0.6:0.6:0,0.15,0" \
  "c4:Standing:0.5:Bip01 Head:0.2,0.4,-1:0.6:0,0.12,0" "c5:Standing:0.5:Bip01 Spine2:0.2,0.15,-1:1.0" \
  "c6:Standing:0.5:Bip01 Spine2:0.3,0.1,1:0.6" "c7:Standing:0.5:Bip01 L Forearm:0.4,-1,0.6:0.55" \
  "c8:Walking:0.4:Bip01 L Foot:0.6,0.3,1:0.8:0,0.25,0" "c9:Death:1.2:Bip01 Spine2:0.5,1,0.5:1.1" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_honkf_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_honkf_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
