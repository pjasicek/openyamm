#!/usr/bin/env bash
# m178 numeric gates on the timed rig (default work/rig_v5.blend): G6 contacts (closed-skin inside test, half frames),
# G4/G5 edge stretch per region, soles, jerk. Logs in work/gate_*.log; prints the summary lines.
set -uo pipefail
cd "$(dirname "$0")/.."
BL=${1:-work/rig_v5.blend}
A="Standing Walking Running Attack Hit Death Fidget"
B=/snap/bin/blender; F="--background --factory-startup --threads 2 --python-exit-code 1 --python"
$B $F scripts/g6_contacts.py -- $BL $A > work/gate_g6.log 2>&1 &
$B $F scripts/stretch_all.py -- $BL $A > work/gate_g4.log 2>&1 &
( $B $F scripts/sole_probe.py -- $BL $A > work/gate_sole.log 2>&1; $B $F scripts/jerk_probe.py -- $BL $A > work/gate_jerk.log 2>&1 ) &
wait
grep -hE "^(G6|G4|SOLE|JERK)" work/gate_g6.log work/gate_g4.log work/gate_sole.log work/gate_jerk.log | cut -c1-400
