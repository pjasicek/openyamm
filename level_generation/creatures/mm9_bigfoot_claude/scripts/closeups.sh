#!/bin/bash
# Joint close-ups in the viewer, framed on the joint. scripts/closeups.sh <tier> <prefix>
t=$1; p=$2; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=export/mm9_bigfoot.glb
spec() { $G scripts/close_specs.py $g "$@" 2>/dev/null | tr '\n' ' '; }
S=""
S+=$(spec ${p}cr AttackMelee:0.40 "Bip01 L Calf:0.5,0.1,1:0.9" "Bip01 R Calf:-0.5,0.1,1:0.9" "Bip01 Spine:0.2,-0.5,1:1.0" "Bip01 R UpperArm:-0.8,-0.3,0.7:0.8" "Bip01 L UpperArm:0.8,-0.3,0.7:0.8" "Bip01 R Forearm:-0.8,0.1,0.5:0.7" "Bip01 Spine3:0.5,0.2,1:0.8" "Bip01 Head:0.1,0,1:0.7")
S+=$(spec ${p}de Death:0.8 "Bip01 L Calf:0.5,0.4,1:0.9" "Bip01 R Calf:-0.5,0.4,1:0.9" "Bip01 Spine:0.2,-0.6,1:1.0" "Bip01 R UpperArm:-0.6,0.6,0.7:0.8" "Bip01 L UpperArm:0.6,0.6,0.7:0.8" "Bip01 L Forearm:0.5,0.6,0.5:0.7" "Bip01 Spine3:0.3,0.8,0.5:0.8" "Bip01 Head:0.1,0.8,0.6:0.7")
S+=$(spec ${p}dd Dead:0.5 "Bip01 L Calf:0.3,1,0.3:0.9" "Bip01 R Calf:-0.3,1,0.3:0.9" "Bip01 Spine:0,1,0.6:1.1" "Bip01 R UpperArm:-0.5,1,0.3:0.8" "Bip01 L UpperArm:0.5,1,0.3:0.8" "Bip01 L Forearm:0.3,1,0.2:0.7" "Bip01 Spine3:0.2,1,0.5:0.8" "Bip01 Head:0.1,1,0.2:0.7")
scripts/vsr.sh $t review/shots $S
