#!/usr/bin/env bash
# Source project's gates on GLB gate copies of the rollback source and the reduced export (same 30 fps import and the
# master's garment/piece labels on both, so the columns compare): gates.py (arm/hand/robe stretch, wrist, hand in
# body, floor; BODY_GARMENTS as its rebuild.sh), rifle_up_check.py, sole_probe.py and head_bob.py (m178 copies).
# Logs work/gate_<label>_*.log, review/gates_<label>.json, review/rifle_up_<label>.json.
set -uo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 2 --python-exit-code 1"
P=level_generation/creatures/hes_guard_reduce_claude
M=../hes_guard_claude/work/rig_v5.blend
A="Standing Walking Running Attack Hit Death Fidget"
for lab in source reduced; do
  glb=work/hes_guard_source_pre_reduce.glb; [ $lab = reduced ] && glb=export/hes_guard.glb
  REA_GLB=$P/$glb REA_NODE=HGD REA_OUT=work/gate_$lab.blend $BL -P scripts/gate_import.py 2>&1 | grep -E "^(WELD|TRIS|PIECES|ACTIONS)|Error" | cut -c1-200
  $BL -P scripts/gate_labels.py -- work/gate_$lab.blend $M 2>&1 | grep -E "GATELABELS|Error"
done
for lab in source reduced; do
  ( BODY_GARMENTS=0,1,15 $BL -P scripts/gates.py -- work/gate_$lab.blend $lab $A > work/gate_${lab}_gates.log 2>&1 ) &
  p1=$!
  ( $BL -P scripts/rifle_up_check.py -- work/gate_$lab.blend $A > work/gate_${lab}_rifle.log 2>&1; cp review/rifle_up.json review/rifle_up_$lab.json ) &
  p2=$!
  ( $BL -P scripts/sole_probe.py -- work/gate_$lab.blend $A > work/gate_${lab}_sole.log 2>&1 ) &
  p3=$!
  wait $p1 $p2 $p3
done
for lab in source reduced; do
  echo "== $lab"; python3 scripts/gates_summary.py $lab | cut -c1-330
  grep -hE "^(RIFLEUP|SOLE)" work/gate_${lab}_rifle.log work/gate_${lab}_sole.log | cut -c1-260
done
