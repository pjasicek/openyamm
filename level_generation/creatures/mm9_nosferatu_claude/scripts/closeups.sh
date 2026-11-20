#!/bin/bash
# Joint close-ups in the viewer, framed on the joint. scripts/closeups.sh <tier id> <prefix>
. scripts/env.sh
t=$1; p=$2; g=export/mm9_nosferatu.glb
spec() { $PYG -W ignore scripts/close_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
S=""
S+=$(spec ${p}cr AttackRanged:0.75 "Bip01 L Calf:0.5,0.1,1:0.7" "Bip01 R Calf:-0.5,0.1,1:0.7" "Bip01 Pelvis:0.2,-0.5,1:0.8" "Bip01 R UpperArm:-0.8,-0.3,0.7:0.55" "Bip01 L UpperArm:0.8,-0.3,0.7:0.55" "Bip01 R Forearm:-0.8,0.1,0.5:0.55" "Bip01 Neck:0.5,0.2,1:0.55" "Bip01 Head:0.1,0,1:0.5")
S+=$(spec ${p}ra Running:0.2 "Bip01 L Calf:0.6,0.2,1:0.8" "Bip01 R Calf:-0.6,0.2,1:0.8" "Bip01 Pelvis:0.3,-0.4,1:0.8")
S+=$(spec ${p}fi Fidget:1.0 "Bip01 R UpperArm:-0.8,-0.5,0.6:0.55" "Bip01 L UpperArm:0.8,-0.5,0.6:0.55" "Bip01 L Forearm:0.8,0.1,0.5:0.55" "Bip01 Neck:0.4,-0.2,1:0.55")
S+=$(spec ${p}de Death:1.0 "Bip01 L Calf:0.5,0.4,1:0.8" "Bip01 R Calf:-0.5,0.4,1:0.8" "Bip01 Pelvis:0.2,0.7,1:0.9" "Bip01 R UpperArm:-0.6,0.6,0.7:0.6" "Bip01 L UpperArm:0.6,0.6,0.7:0.6" "Bip01 L Forearm:0.5,0.6,0.5:0.55" "Bip01 Neck:0.3,0.8,0.5:0.55" "Bip01 Head:0.1,0.8,0.6:0.5")
S+=$(spec ${p}dd Dead:0.5 "Bip01 L Calf:0.3,1,0.3:0.9" "Bip01 R Calf:-0.3,1,0.3:0.9" "Bip01 Pelvis:0,1,0.6:1.0" "Bip01 R UpperArm:-0.5,1,0.3:0.6" "Bip01 L UpperArm:0.5,1,0.3:0.6" "Bip01 L Forearm:0.3,1,0.2:0.55" "Bip01 Neck:0.2,1,0.5:0.55" "Bip01 Head:0.1,1,0.2:0.5")
S+=$(spec ${p}st Standing:0.5 "Bip01 Head:0.0,0.05,1:0.5" "Bip01 Head:0.8,0.1,0.8:0.55" "Bip01 Head:-0.8,0.1,0.8:0.55" "Bip01 L Hand:0.6,-0.1,0.8:0.4" "Bip01 R Hand:-0.6,-0.1,0.8:0.4" "Bip01 Head:0.0,-0.25,1:0.32")
scripts/vs2.sh $t review/shots $S
