#!/bin/bash
# Joint close-ups in the viewer, framed on the named joint from outside the body: knees, groin, armpits, elbows, neck, mouth in the
# crouch (AttackMelee at its low point), the kneel (Death2 1.0 s), the fall (Death 1.2 s) and Dead. Project folder.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=export/mm9_yanmir.glb
spec() { $G scripts/close_specs.py $g "$@" 2>/dev/null | tr '\n' ' '; }
S=""
S+=$(spec ccr AttackMelee:0.55 "Bip01 L Calf:0.5,0.1,1:0.9" "Bip01 R Calf:-0.5,0.1,1:0.9" "Bip01 Spine:0.2,-0.5,1:1.0" "Bip01 R UpperArm:-0.8,-0.3,0.7:0.8" "Bip01 L UpperArm:0.8,-0.3,0.7:0.8" "Bip01 L Forearm:0.8,0.1,0.5:0.7" "Bip01 Neck:0.5,0.2,1:0.8" "Bip01 Head:0.1,0,1:0.6")
S+=$(spec ckn Death2:1.0 "Bip01 L Calf:0.5,0.3,1:0.9" "Bip01 R Calf:-0.5,0.3,1:0.9" "Bip01 Spine:0.2,-0.6,1:1.0" "Bip01 R UpperArm:-0.8,0.2,0.7:0.8" "Bip01 L UpperArm:0.8,0.2,0.7:0.8" "Bip01 R Forearm:-0.6,0.3,0.6:0.7" "Bip01 Neck:0.3,0.6,0.8:0.8" "Bip01 Head:0.1,0.4,1:0.6")
S+=$(spec cde Death:1.2 "Bip01 L Calf:0.5,0.4,1:0.9" "Bip01 R Calf:-0.5,0.4,1:0.9" "Bip01 Spine:0.2,-0.6,1:1.0" "Bip01 R UpperArm:-0.6,0.6,0.7:0.8" "Bip01 L UpperArm:0.6,0.6,0.7:0.8" "Bip01 L Forearm:0.5,0.6,0.5:0.7" "Bip01 Neck:0.3,0.8,0.5:0.8" "Bip01 Head:0.1,0.8,0.6:0.6")
S+=$(spec cdd Dead:0.5 "Bip01 L Calf:0.3,1,0.3:0.9" "Bip01 R Calf:-0.3,1,0.3:0.9" "Bip01 Spine:0,1,0.6:1.1" "Bip01 R UpperArm:-0.5,1,0.3:0.8" "Bip01 L UpperArm:0.5,1,0.3:0.8" "Bip01 L Forearm:0.3,1,0.2:0.7" "Bip01 Neck:0.2,1,0.5:0.8" "Bip01 Head:0.1,1,0.2:0.6")
mkdir -p review/shots
scripts/vsr.sh yanmir review/shots $S
$G scripts/sheet.py review/sheet_closeups.png 8 300 $(ls review/shots | grep -E "^c(cr|kn|de|dd)" | sed 's/.png//')
