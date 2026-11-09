#!/usr/bin/env bash
# The source project's gates (copies: g6_contacts.py, stretch_all.py, sole_probe.py, head_bob.py) on GLB gate copies of
# the rollback source and the reduced export (gate_import.py + gate_attrs.py), same import for both so the numbers
# compare. Logs work/gate_<label>_<gate>.log; JSON outputs copied to work/<gate>_<label>.json.
set -uo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 2 --python-exit-code 1"
P=level_generation/creatures/mm7_m178_reduce_claude
A="Standing Walking Running Attack Hit Death Fidget"
for lab in source reduced; do
  glb=work/mm7_m178_source_pre_reduce.glb; [ $lab = reduced ] && glb=export/mm7_m178.glb
  REA_GLB=$P/$glb REA_NODE=Devil REA_OUT=work/gate_$lab.blend $BL -P scripts/gate_import.py 2>&1 | grep -E "^(WELD|TRIS|PIECES)|Error"
  $BL -P scripts/gate_attrs.py -- work/gate_$lab.blend 2>&1 | grep -E "GATEATTRS|Error"
done
for lab in source reduced; do
  ( $BL -P scripts/g6_contacts.py -- work/gate_$lab.blend $A > work/gate_${lab}_g6.log 2>&1; cp work/g6_contacts.json work/g6_contacts_$lab.json ) &
  pid1=$!
  ( $BL -P scripts/stretch_all.py -- work/gate_$lab.blend $A > work/gate_${lab}_g4.log 2>&1; cp work/stretch_all.json work/stretch_all_$lab.json ) &
  pid2=$!
  ( $BL -P scripts/sole_probe.py -- work/gate_$lab.blend $A > work/gate_${lab}_sole.log 2>&1;
    $BL -P scripts/head_bob.py -- work/gate_$lab.blend $A > work/gate_${lab}_bob.log 2>&1 ) &
  pid3=$!
  wait $pid1 $pid2 $pid3
done
for lab in source reduced; do
  echo "== $lab"; grep -hE "^(G6|G4|SOLE|HEADBOB)" work/gate_${lab}_g6.log work/gate_${lab}_g4.log work/gate_${lab}_sole.log work/gate_${lab}_bob.log | cut -c1-330
done
