#!/usr/bin/env bash
# Source project's gates (copies: g4_weights.py, g5_hand_stretch.py, g6_contacts.py, sole_probe.py, jerk_probe.py) on
# GLB gate copies of the rollback source and the reduced export: same 30 fps import and the master's garment/piece/
# finger labels (gate_labels.py from ../hes_villager_m_claude/work/rig_v5.blend) on both, so the columns compare.
# Logs work/gate_<label>_*.log; summary work/gates_final.txt.
set -uo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 2 --python-exit-code 1"
P=level_generation/creatures/hes_villager_m_reduce_claude
M=../hes_villager_m_claude/work/rig_v5.blend
CLIPS="Standing:90 Walking:30 Hit:30 Death:138 Fidget:153"
ACTS=$(for c in $CLIPS; do echo -n "${c%%:*} "; done)
PK=(); for c in $CLIPS; do n=${c#*:}; a=${c%%:*}; for f in $(seq 0 3 $n); do PK+=("$a:$f"); done; done
for lab in source reduced; do
  glb=work/hes_hvm_source_pre_reduce.glb; [ $lab = reduced ] && glb=export/hes_hvm.glb
  REA_GLB=$P/$glb REA_NODE=HVM REA_OUT=work/gate_$lab.blend $BL -P scripts/gate_import.py 2>&1 | grep -E "^(TRIS|PIECES)|Error" | cut -c1-200
  $BL -P scripts/gate_labels.py -- work/gate_$lab.blend $M 2>&1 | grep -E "GATELABELS|Error"
done
for lab in source reduced; do
  ( $BL -P scripts/g4_weights.py -- work/gate_$lab.blend $lab "${PK[@]}" > work/gate_${lab}_g4.log 2>&1 ) & p1=$!
  ( $BL -P scripts/g5_hand_stretch.py -- work/gate_$lab.blend $ACTS > work/gate_${lab}_g5.log 2>&1 ) & p2=$!
  ( $BL -P scripts/g6_contacts.py -- work/gate_$lab.blend $ACTS > work/gate_${lab}_g6.log 2>&1 ) & p3=$!
  ( $BL -P scripts/sole_probe.py -- work/gate_$lab.blend $ACTS > work/gate_${lab}_sole.log 2>&1 ) & p4=$!
  wait $p1 $p2 $p3 $p4
done
for lab in source reduced; do
  echo "== $lab"
  python3 - work/gate_${lab}_g4.log <<'PY'
import re, sys
best = {}
for l in open(sys.argv[1]):
    m = re.match(r"G4 (\S+):(\d+)\s+(\S+): stretch p99 ([\d.]+) max ([\d.]+)", l)
    if m:
        k = (m.group(1), m.group(3)); p, mx = float(m.group(4)), float(m.group(5))
        if k not in best or p > best[k][0]: best[k] = (p, mx, int(m.group(2)))
for (a, s), (p, mx, f) in sorted(best.items()): print(f"G4 {a:8s} {s}: worst p99 {p} (max {mx}) at frame {f}")
PY
  grep -hE "^(G5|HANDSTRETCH|G6|CONTACT|SOLE)" work/gate_${lab}_g5.log work/gate_${lab}_g6.log work/gate_${lab}_sole.log | cut -c1-240
done | tee work/gates_final.txt
