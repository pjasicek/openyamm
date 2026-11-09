#!/usr/bin/env bash
# m246 gates on the gated master (default work/rig_v5.blend): G4 arm weights (every 6th frame of each clip), G5 hand
# stretch, G6 contacts, head clearance, skirt stretch/poke, soles, jerk. Output: review/gates.txt (also printed).
set -uo pipefail
cd "$(dirname "$0")/.."
P=$(pwd); R=$P/../../..
: "${TOKEN:?set TOKEN}"
B=${1:-$P/work/rig_v5.blend}
ACTS="Standing Walking Running Attack Hit Fidget Death"
OUT=$P/review/gates.txt; : > "$OUT"
run() { local s=$1; shift; local out log
        out=$(cd "$R" && tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$(basename "$P")/scripts/$s" "$@" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        grep -A8 Traceback "$log" | tail -10
        grep -E '^(G4|G5|G6|HANDSTRETCH|HEADCLEAR|SKIRT|POKE|SOLE|JERK|BLADE)' "$log" | cut -c1-400 | tee -a "$OUT"; }
PICKS=$(python3 - "$B" <<'PY'
# every 6th frame of each clip (frame ranges from the clip_timing export are not known here: use generous ranges)
import sys
r = {'Standing': 90, 'Walking': 30, 'Running': 22, 'Attack': 55, 'Hit': 15, 'Fidget': 71, 'Death': 66}
print(' '.join(f'{a}:{f}' for a, n in r.items() for f in range(0, n + 1, 6)))
PY
)
run g4_weights.py "$B" final $PICKS
run g5_hand_stretch.py "$B" $ACTS
run g6_contacts.py "$B" $ACTS
run g6_head_clearance.py "$B" $ACTS
run g4_skirt.py "$B" $ACTS
run g6_skirt_poke.py "$B" $ACTS
run sole_probe.py "$B" $ACTS
run jerk_probe.py "$B" $ACTS
