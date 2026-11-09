#!/usr/bin/env bash
# Source project's gates (copies: gates.py, g6_leg_leak.py, g6_hand_proximity.py, sole_probe.py) on GLB gate copies of
# the rollback source and the reduced export: same 30 fps import and the master's garment/piece/finger labels
# (gate_labels.py from ../hes_villager_f_claude/work/rig_v5.blend) on both, so the columns compare.
# Writes review/gates_<label>.json, review/g6_legs_<label>.json, review/g6_hands_<label>.json; summary work/gates_final.txt.
# Usage: scripts/gates.sh [reduced glb, default export/hes_villager_f.glb] [label, default reduced]
set -uo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 2 --python-exit-code 1"
P=level_generation/creatures/hes_villager_f_reduce_claude
M=../hes_villager_f_claude/work/rig_v5.blend
RG=${1:-export/hes_villager_f.glb}; RL=${2:-reduced}; LABS="${LABS:-source $RL}"
A="Standing Walking Hit Death Fidget"
for lab in $LABS; do
  glb=work/hes_villager_f_source_pre_reduce.glb; [ $lab = $RL ] && glb=$RG
  REA_GLB=$P/$glb REA_NODE=HVF REA_OUT=work/gate_$lab.blend $BL -P scripts/gate_import.py 2>&1 | grep -E "^(TRIS)|Error" | cut -c1-200
  $BL -P scripts/gate_labels.py -- work/gate_$lab.blend $M 2>&1 | grep -E "GATELABELS|Error"
done
for lab in $LABS; do
  ( BODY_GARMENTS=0,1,2 $BL -P scripts/gates.py -- work/gate_$lab.blend $lab $A > work/gate_${lab}_gates.log 2>&1 ) & p1=$!
  ( $BL -P scripts/g6_leg_leak.py -- work/gate_$lab.blend $lab $A > work/gate_${lab}_legs.log 2>&1 ) & p2=$!
  ( $BL -P scripts/g6_hand_proximity.py -- work/gate_$lab.blend $lab $A Dead > work/gate_${lab}_hands.log 2>&1 ) & p3=$!
  ( $BL -P scripts/sole_probe.py -- work/gate_$lab.blend $A > work/gate_${lab}_sole.log 2>&1 ) & p4=$!
  wait $p1 $p2 $p3 $p4
done
for lab in $LABS; do
  echo "== $lab"; python3 scripts/gates_summary.py $lab | cut -c1-330
  grep -hE "^(G6LEGS|G6HANDS|SOLE)" work/gate_${lab}_legs.log work/gate_${lab}_hands.log work/gate_${lab}_sole.log | cut -c1-300
done | tee work/gates_final_$RL.txt
