#!/usr/bin/env bash
# Gates of the source project (copies of mm7_m246_claude/scripts: g4_weights, g5_hand_stretch, g6_contacts,
# g6_head_clearance, g6_crest, g4_skirt, g6_skirt_poke, sole_probe) on a gate copy of a GLB: gate_import.py (weld,
# Body/Rig names) + gate_attrs.py (garment/finger/piece labels from the master work/rig_v6.blend).
# Usage: TOKEN=<lease> scripts/gates.sh <glb> <label>  -> work/gate_<label>.blend, review/gates_<label>.txt
set -uo pipefail
cd "$(dirname "$0")/.."
P=$(pwd); glb=$(realpath "$1"); label=$2; B=$P/work/gate_$label.blend; OUT=$P/review/gates_$label.txt; : > "$OUT"
REA_GLB=$glb REA_NODE=M246 REA_OUT=work/gate_$label.blend PAT="^(WELD|TRIS)" scripts/b.sh gate_import.py | tee -a "$OUT"
PAT="^GATEATTRS" scripts/b.sh gate_attrs.py "$B" "$P/../mm7_m246_claude/work/rig_v6.blend" | tee -a "$OUT"
ACTS="Standing Walking Running Attack Hit Fidget Death"
PICKS=$(python3 -c "
r = {'Standing': 72, 'Walking': 24, 'Running': 17, 'Attack': 57, 'Hit': 12, 'Fidget': 56, 'Death': 52}
print(' '.join(f'{a}:{f}' for a, n in r.items() for f in range(0, n + 1, 4)))")
run() { PAT='^(G4|G5|G6|HANDSTRETCH|HEADCLEAR|SKIRT|POKE|SOLE|CREST)' scripts/b.sh "$@" | tee -a "$OUT"; }
run g4_weights.py "$B" "$label" $PICKS > /dev/null
run g5_hand_stretch.py "$B" $ACTS
run g6_contacts.py "$B" $ACTS
run g6_head_clearance.py "$B" $ACTS
run g6_crest.py "$B" $ACTS
run g4_skirt.py "$B" $ACTS
STRIPS=1,2 run g4_skirt.py "$B" $ACTS
run g6_skirt_poke.py "$B" $ACTS
run sole_probe.py "$B" $ACTS
