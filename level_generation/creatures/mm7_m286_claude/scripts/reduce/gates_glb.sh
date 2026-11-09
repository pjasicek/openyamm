#!/usr/bin/env bash
# Arm and hand gate (the project's scripts/gates.sh steps on a gate_blend.py copy: G6 contacts with the axe, G5 hand
# stretch, G4 arm stretch, soles, foot flatness) for a runtime-equivalent body + axe. TOKEN=<lease>.
# Usage: gates_glb.sh <label> <blend> <object> <axe glb>  -> review/shots/reduction/gates_<label>.txt
set -euo pipefail
cd "$(dirname "$0")/../.."; P=level_generation/creatures/mm7_m286_claude; ROOT=$(cd ../../.. && pwd); W=$PWD/work
label=$1; OUT=$PWD/review/shots/reduction/gates_$label.txt; export FINGERS=${FINGERS:-1,2,4}
CLIPS="Standing Walking Running Attack Hit Fidget Death"
BL_GREP=GATEBLEND scripts/reduce/bl.sh gate_blend.py "$PWD/$2" "$3" "$PWD/$4" "$W/gate_$label.blend"
run() { local out log; out=$(cd "$ROOT" && tools/run_creature_blender.sh --token "$TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        grep -E '^(G6|HANDSTRETCH|SOLE|G4|FLAT|STAND|Traceback|Error)' "$log" | cut -c1-400 || true; }
{
PROP_HAND=R run g6_prop.py "$W/gate_$label.blend" $CLIPS
run g5_hand_stretch.py "$W/gate_$label.blend" $CLIPS
run g4_weights.py "$W/gate_$label.blend" $label Attack:15 Attack:25 Attack:30 Fidget:30 Hit:6 Death:40 Running:10 Walking:10 Standing:0
STEP=0.5 run sole_probe.py "$W/gate_$label.blend" $CLIPS
run foot_flat.py "$W/gate_$label.blend" Standing Walking Running Attack Fidget
} | tee "$OUT"
