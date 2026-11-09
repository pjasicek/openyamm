#!/usr/bin/env bash
# m442 gates on a chain blend (default work/rig_v5.blend): G4 arm stretch on frames every STEP of every clip, G5 hand
# stretch, G6 contacts, tunic poke, soles, jerk. Prints the summary lines. Usage: TOKEN=<lease> scripts/gates.sh [blend]
set -euo pipefail
cd "$(dirname "$0")/.."
P=$(pwd); NAME=$(basename "$P"); BL=${1:-$P/work/rig_v5.blend}
: "${TOKEN:?set TOKEN}"
run() { local s=$1; shift; local out log
        out=$(cd "$P/../../.." && tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$NAME/scripts/$s" "$@" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
        grep -E '^(G4|G5|G6|HANDSTRETCH|SKIRT|POKE|SOLE|JERK|CONTACT)' "$log" | cut -c1-230 || true; }
CLIPS=${CLIPS:-"Standing:90 Walking:30 Hit:30 Death:66 Fidget:153"}
PK=()
for c in $CLIPS; do n=${c#*:}; a=${c%%:*}; for f in $(seq 0 ${STEP:-3} $n); do PK+=("$a:$f"); done; done
[ -n "${SKIP_G4:-}" ] || { run g4_weights.py "$BL" v5 "${PK[@]}" > work/g4_full.txt; python3 - <<'PY'
import re
rows=[l for l in open('work/g4_full.txt') if l.startswith('G4')]
best={}
for l in rows:
    m=re.match(r"G4 (\S+):(\d+)\s+(\S+): stretch p99 ([\d.]+) max ([\d.]+)",l)
    if not m: continue
    a,f,s,p,mx=m.group(1),int(m.group(2)),m.group(3),float(m.group(4)),float(m.group(5))
    k=(a,s); 
    if k not in best or p>best[k][0]: best[k]=(p,mx,f)
for (a,s),(p,mx,f) in sorted(best.items()): print(f"G4 {a:8s} {s}: worst p99 {p} (max {mx}) at frame {f}")
PY
}
ACTS=$(for c in $CLIPS; do echo -n "${c%%:*} "; done)
run g5_hand_stretch.py "$BL" $ACTS
run g6_contacts.py "$BL" $ACTS
run sole_probe.py "$BL" $ACTS
run jerk_probe.py "$BL" $ACTS
