#!/usr/bin/env bash
# Candidate's python gates, then (one Blender at a time) the sleeve gate and LOD checks of the installed file and the candidate.
# Usage: scripts/gates_all.sh <glb> <tag>
cd "$(dirname "$0")/.."
scripts/gates.sh $1 $2 noblender
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
F=/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_honkfemale_claude
$BL --python $F/v2/scripts/sleeve_gate.py -- $(realpath $1) $PWD/review/gates_$2/sleeve_gate.json Bip01 24 front,above34,below,q34 > review/gates_$2/sleeve.txt 2>&1
[[ -f work/lod_check_installed.json ]] || REA_NODE=HonkF $BL -P scripts/lod_check.py -- $(realpath before/mm9_honkf.glb) installed > work/lod_check_installed.log 2>&1
REA_NODE=HonkF $BL -P scripts/lod_check.py -- $(realpath $1) $2 > work/lod_check_$2.log 2>&1
echo ALL > review/gates_$2/all_done.txt
