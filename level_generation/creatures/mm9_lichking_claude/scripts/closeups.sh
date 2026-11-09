#!/bin/bash
# Joint close-ups in the viewer, framed on the joint from outside the body. scripts/closeups.sh <prefix>
p=$1; G=../claude_shared/gltf_venv/bin/python; g=export/mm9_lichking.glb
spec() { $G -W ignore scripts/close_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
S=""
# kneeling (Death2 1.2 s): knees, groin, coat over the heels
S+=$(spec ${p}kn Death2:1.2 "Bip01 L Calf:0.6,0.2,1:0.6" "Bip01 R Calf:-0.6,0.2,1:0.6" "Bip01 Pelvis:0.2,-0.3,1:0.8" "Bip01 Pelvis:0.3,0.2,-1:0.9")
# running crouch
S+=$(spec ${p}ru Running:0.13 "Bip01 L Calf:0.7,0.2,1:0.6" "Bip01 R Calf:-0.7,0.2,1:0.6" "Bip01 Pelvis:0.3,-0.5,1:0.8")
# raised arms (AttackMelee 0.45, Taunt 0.9): armpits, elbows, shoulders
S+=$(spec ${p}am AttackMelee:0.45 "Bip01 R UpperArm:-0.8,-0.4,0.6:0.55" "Bip01 L UpperArm:0.8,-0.4,0.6:0.55" "Bip01 R Forearm:-0.8,0.2,0.5:0.5" "Bip01 L Forearm:0.8,0.2,0.5:0.5")
S+=$(spec ${p}ta Taunt:0.9 "Bip01 R UpperArm:-0.8,-0.4,0.6:0.55" "Bip01 L UpperArm:0.8,-0.4,0.6:0.55" "Bip01 Neck:0.3,0.1,1:0.5")
# death fall and corpse: neck, mouth, knees, elbows
S+=$(spec ${p}de Death:0.6 "Bip01 Neck:0.3,0.6,0.8:0.55" "Bip01 L Calf:0.5,0.6,1:0.6" "Bip01 R Forearm:-0.5,0.6,0.6:0.55")
S+=$(spec ${p}dd Dead:0.5 "Bip01 Head:0.1,1,0.3:0.5" "Bip01 Neck:0.3,1,0.5:0.55" "Bip01 L Calf:0.3,1,0.3:0.6" "Bip01 Pelvis:0,1,0.6:0.9" "Bip01 L UpperArm:0.5,1,0.3:0.55")
S+=$(spec ${p}d2 Dead2:0.5 "Bip01 Head:0.1,1,0.3:0.5" "Bip01 Pelvis:0,1,0.6:0.9" "Bip01 L Calf:0.3,1,0.3:0.6")
# head and mouth at full size, standing
S+=$(spec ${p}hd Standing:0.5 "Bip01 Head:0,0.05,1:0.45" "Bip01 Head:0.8,0.15,0.8:0.45" "Bip01 Head:-1,0.1,0.1:0.45" "Bip01 Head:0,0.25,1:0.25")
bash scripts/vs.sh lichking review/shots $S
