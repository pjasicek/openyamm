#!/bin/bash
# Joint close-ups in the viewer, framed on the joint from outside the body. scripts/closeups.sh <tier id> <prefix>
t=$1; p=$2; G=../claude_shared/gltf_venv/bin/python; g=export/mm9_ebora.glb
spec() { $G -W ignore scripts/close_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
S=""
# crouch before take-off (Launch 0.3): knees, groin, hips
S+=$(spec ${p}cr Launch:0.30 "Bip01 L Calf:0.5,0.1,1:0.55" "Bip01 R Calf:-0.5,0.1,1:0.55" "Bip01 Pelvis:0.2,-0.5,1:0.75" "Bip01 Pelvis:0.1,0.3,-1:0.75")
S+=$(spec ${p}ra Running:0.20 "Bip01 L Calf:0.6,0.2,1:0.55" "Bip01 R Calf:-0.6,0.2,1:0.55" "Bip01 Pelvis:0.3,-0.4,1:0.75")
# arms raised over the head (AttackRanged 0.4): armpits, elbows, neck
S+=$(spec ${p}ar AttackRanged:0.40 "Bip01 R UpperArm:-0.8,-0.2,0.7:0.5" "Bip01 L UpperArm:0.8,-0.2,0.7:0.5" "Bip01 R Forearm:-0.8,0.1,0.5:0.5" "Bip01 L Forearm:0.8,0.1,0.5:0.5" "Bip01 Neck:0.4,0.2,1:0.5")
S+=$(spec ${p}de Death:0.96 "Bip01 L Calf:0.5,0.4,1:0.55" "Bip01 R Calf:-0.5,0.4,1:0.55" "Bip01 Pelvis:0.2,0.7,1:0.8" "Bip01 L UpperArm:0.6,0.6,0.7:0.55" "Bip01 R UpperArm:-0.6,0.6,0.7:0.55" "Bip01 L Forearm:0.5,0.6,0.5:0.5" "Bip01 Neck:0.3,0.8,0.5:0.5")
S+=$(spec ${p}dd Dead:0.5 "Bip01 L Calf:0.3,1,0.3:0.55" "Bip01 R Calf:-0.3,1,0.3:0.55" "Bip01 Pelvis:0,1,0.6:0.85" "Bip01 L Forearm:0.3,1,0.2:0.5" "Bip01 Neck:0.2,1,0.5:0.5" "Bip01 Head:0.1,1,0.2:0.45" "Bip01 Spine2:0,1,-0.5:1.3")
S+=$(spec ${p}hd Standing:0.5 "Bip01 Head:0.0,0.05,1:0.42" "Bip01 Head:0.8,0.1,0.8:0.45" "Bip01 Head:1,0.05,0:0.45" "Bip01 Head:0,0.1,-1:0.45" "Bip01 L Hand:0.6,-0.1,0.8:0.35" "Bip01 R Hand:-0.6,-0.1,0.8:0.35")
# wing roots and the folded wing from behind (Standing), spread wing (Fly)
S+=$(spec ${p}wg Standing:0.5 "Bip01 Spine2:0,0.3,-1:0.9" "Bip01 Spine2:0.7,0.6,-0.7:1.2" "Bip01 Spine3:-1,0.3,-0.3:1.0")
S+=$(spec ${p}wf Fly:0.25 "Bip01 Spine2:0,0.4,-1:2.2" "Bip01 Spine2:0,0.3,1:2.2")
scripts/vs.sh $t review/shots $S
