#!/bin/bash
# Close viewer shots of the reduced regions, installed vs reduced: hands (Standing both, AttackMelee R, Fidget L at the face),
# sleeves (Fidget elbow), boots, the back of the head (hair shell), the nape, the corpse. Usage: scripts/close_shots.sh [models]
# -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python
C=$($G -W ignore scripts/close_specs.py before/mm9_honkm.glb \
  "c0:Standing:0.5:Bip01 L Hand:1,0.2,0.6:0.45" "c1:Standing:0.5:Bip01 R Hand:-1,0.2,0.6:0.45" \
  "c2:AttackMelee:0.5:Bip01 R Hand:-0.4,0.3,1:0.5" "c3:Fidget:1.0:Bip01 L Hand:0.6,0.2,1:0.5" \
  "c4:Fidget:1.0:Bip01 R Forearm:-1,0.2,0.3:0.7" "c5:Walking:0.4:Bip01 Spine:0.7,0.1,0.7:0.8" \
  "c6:Standing:0.5:Bip01 R Foot:-0.5,0.4,1:0.6:0,0.15,0" "c7:Standing:0.5:Bip01 Head:0.3,0.3,-1:0.55:0,0.08,0" \
  "c8:Standing:0.5:Bip01 Head:-1,0.1,-0.3:0.55:0,0.08,0" "c9:Death:1.2:Bip01 Spine2:0.5,1,0.5:1.1" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_honkm_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_honkm_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
