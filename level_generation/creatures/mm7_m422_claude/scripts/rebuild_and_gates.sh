#!/usr/bin/env bash
# anim stage + every gate on rig_v5 (G4/G5/G6 gates.py, cloth, soles, jerk). Usage: TOK=<lease> scripts/rebuild_and_gates.sh [stage]
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD; NAME=$(basename "$P"); REPO=$(cd ../../.. && pwd)
bash scripts/rebuild.sh ${1:-anim}
g() { local out log; out=$(cd "$REPO" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$NAME/scripts/$1" "${@:2}" 2>&1) || true
      log=$(echo "$out" | grep "Blender log" | awk '{print $3}'); grep -E '^(CLOTH|SOLE|JERK|FOOT|ARMPIT|[A-Z]+ )' "$log" | cut -c1-260 || true
      if grep -q "Traceback" "$log"; then grep -A12 Traceback "$log" | head -20; exit 1; fi; }
g cloth_gates.py "$P/work/rig_v5.blend" v5
g armpit_stretch.py "$P/work/rig_v5.blend" v5
STEP=0.5 g sole_probe.py "$P/work/rig_v5.blend" Standing Walking Attack Hit Fidget Death
g jerk_probe.py "$P/work/rig_v5.blend" Standing Walking Attack Hit Fidget Death
