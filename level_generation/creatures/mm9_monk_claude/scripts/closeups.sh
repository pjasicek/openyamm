#!/bin/bash
# Joint close-ups in the viewer, framed on the joint. scripts/closeups.sh <tier id> <prefix>
t=$1; p=$2; G=../claude_shared/gltf_venv/bin/python; g=export/mm9_monk.glb
spec() { $G -W ignore scripts/close_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
S=""
# neck, armpits, elbows, waist in bends; the robe has no knees or groin to see, its knees are the kneeling cloth in Pray and the hem in the corpse
S+=$(spec ${p}pr Pray:0.7 "Bip01 Spine:0.5,0.2,1:0.75" "Bip01 L Calf:0.5,0.1,1:0.6" "Bip01 R Calf:-0.5,0.1,1:0.6" "Bip01 R UpperArm:-0.8,-0.3,0.7:0.5" "Bip01 L UpperArm:0.8,-0.3,0.7:0.5" "Bip01 R Forearm:-0.7,-0.2,0.7:0.42" "Bip01 Neck:0.3,0.1,1:0.45")
S+=$(spec ${p}co Cower:0.4 "Bip01 Spine:0.2,-0.4,1:0.75" "Bip01 R UpperArm:-0.8,-0.3,0.7:0.5" "Bip01 L Forearm:0.7,0.1,0.7:0.42" "Bip01 Neck:0.4,0.5,1:0.45")
S+=$(spec ${p}ra Running:0.2 "Bip01 L Calf:0.6,0.2,1:0.6" "Bip01 R Calf:-0.6,0.2,1:0.6" "Bip01 Spine:0.3,-0.4,1:0.75")
S+=$(spec ${p}ar AttackRanged3:0.9 "Bip01 R UpperArm:-0.8,-0.5,0.3:0.5" "Bip01 L UpperArm:0.8,-0.5,0.3:0.5" "Bip01 L Forearm:0.8,0.1,0.5:0.45" "Bip01 Neck:0.4,0.1,1:0.45")
S+=$(spec ${p}de Death:1.0 "Bip01 Spine:0.2,0.7,1:0.8" "Bip01 R UpperArm:-0.6,0.6,0.7:0.55" "Bip01 L UpperArm:0.6,0.6,0.7:0.55" "Bip01 L Forearm:0.5,0.6,0.5:0.5" "Bip01 Neck:0.3,0.8,0.6:0.5")
S+=$(spec ${p}dd Dead:0.5 "Bip01 L Calf:0.3,1,0.3:0.65" "Bip01 R Calf:-0.3,1,0.3:0.65" "Bip01 L Foot:0.1,0.6,0.1:0.7" "Bip01 Spine:0,1,0.6:0.85" "Bip01 R UpperArm:-0.5,1,0.3:0.55" "Bip01 L UpperArm:0.5,1,0.3:0.55" "Bip01 Neck:0.3,1,0.6:0.5")
S+=$(spec ${p}st Standing:0.5 "Bip01 Head:0.0,0.05,1:0.42" "Bip01 Head:0.8,0.1,0.8:0.45" "Bip01 Head:-0.8,0.1,0.8:0.45" "Bip01 L Hand:0.6,-0.1,0.8:0.35" "Bip01 R Hand:-0.6,-0.1,0.8:0.35" "Bip01 R Forearm:-0.5,-0.3,0.9:0.45" "Bip01 L UpperArm:0.8,-0.3,0.6:0.5")
scripts/vs.sh $t review/shots $S
