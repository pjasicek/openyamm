#!/usr/bin/env bash
# hkr numeric gates on the final chain (work/rig_v3t.blend), every clip: G4 arm stretch, G5 hand stretch, wrist swing
# and twist, hands in the body (gates.py), the carbine's up axis (rifle_up_check.py), soles (sole_probe.py), motion
# jerk (jerk_probe.py), walk/run strides (stride.py); the armour gate runs in rebuild.sh (review/armour_gate_a3.json).
# Usage: TOK=<lease> scripts/gates_hkr.sh   -> work/gates_final.txt
set -uo pipefail
cd "$(dirname "$0")/.."
P=$PWD; S=scripts/step.sh; B=$P/work/rig_v3t.blend
CLIPS="Standing Walking Running Attack Hit Fidget Death"
{
BODY_GARMENTS=0,3,16 $S gates.py $B final $CLIPS > /dev/null; python3 scripts/gates_summary.py final
$S rifle_up_check.py $B $CLIPS
STEP=0.5 $S sole_probe.py $B $CLIPS
$S jerk_probe.py $B Standing Walking Running Attack Hit Fidget
$S stride.py $B Walking Running
$S silhouette_ratio.py $B
$S hip_flex_probe.py $B Running
python3 scripts/gate_table.py a3
$S shell_stretch.py $B $P/scripts/armour_trooper.json final $CLIPS | tail -1
$S shell_leak.py $B $P/scripts/armour_trooper.json final $CLIPS
} 2>&1 | tee work/gates_final.txt
