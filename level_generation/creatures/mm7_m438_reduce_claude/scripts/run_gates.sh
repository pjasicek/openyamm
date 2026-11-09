#!/usr/bin/env bash
# The m438 gates (copies of ../mm7_m438_claude/scripts: g4_weights.py, g5_hand_stretch.py, g6_prop.py with PROP_HAND=L,
# sole_probe.py) on a gate copy built by gate_import.py + gate_attrs.py + gate_prop.py -> review/gates_<label>.txt.
# G4 uses the frames of the production run (work/g4_final.json keys of ../mm7_m438_claude). Usage: TOKEN=<lease> run_gates.sh <label>
set -euo pipefail
cd "$(dirname "$0")/.."
lab=$1; B=$PWD/work/gate_$lab.blend; out=review/gates_$lab.txt
picks=$(python3 -c "import json; print(' '.join(json.load(open('../mm7_m438_claude/work/g4_final.json'))))")
ACTS="Standing Walking Running Attack Hit Death Fidget"
{
echo "# m438 reduction gates on work/gate_$lab.blend"
echo "== G4"; PAT='^G4' scripts/b.sh g4_weights.py $B $lab $picks
echo "== G5"; PAT='^HANDSTRETCH' scripts/b.sh g5_hand_stretch.py $B $ACTS
echo "== G6"; PROP_HAND=L PAT='^G6BOW' scripts/b.sh g6_prop.py $B $ACTS; cp work/g6_bow.json work/g6_$lab.json
echo "== soles"; PAT='^SOLE' scripts/b.sh sole_probe.py $B $ACTS
} > $out 2>&1
cat $out
