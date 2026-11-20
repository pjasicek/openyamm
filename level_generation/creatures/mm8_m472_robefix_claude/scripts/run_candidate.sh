#!/usr/bin/env bash
# One Run2 candidate (robefix 2026-11-12), from the repository root:
#   RF_TAG=<tag> RF_FIT='<json>' RF_PAD='<json>' RF_HEM=<m> scripts/run_candidate.sh <token>
# Blender (one at a time): gait2_motion -> gait2_cloth -> gait2_export; then the graft onto the installed GLB backup
# (work/before_robefix/mm8_m472.glb) -> work/<tag>/mm8_m472.glb and its motion audit -> work/<tag>/audit/.
set -euo pipefail
: "${RF_NOCLEAR:=0}" "${RF_SMOOTH:=0}"
P=level_generation/creatures/mm8_m472_robefix_claude
TOKEN=$1
export RF_TAG RF_FIT RF_PAD RF_HEM RF_NOCLEAR RF_SMOOTH
mkdir -p "$P/work/$RF_TAG"
for s in gait2_motion gait2_cloth gait2_export; do
    out=$(tools/run_creature_blender.sh --token "$TOKEN" "$P/scripts/$s.py" 2>&1 || true)
    log=$(printf '%s\n' "$out" | sed -n 's/^Blender log: //p')
    cp "$log" "$P/work/$RF_TAG/$s.log"
    if grep -q Traceback "$log"; then grep -A30 Traceback "$log" | tail -30; exit 1; fi
    grep -E "GAIT2|GARMENT_SIM|SURFACE_CLEARANCE|Error|Traceback" "$log" | tail -8 || true
done
cp "$P/work/deformation.json" "$P/work/$RF_TAG/deformation.json"
python3 "$P/scripts/gait2_graft.py" "$P/work/before_robefix/mm8_m472.glb" "$P/work/$RF_TAG/mm8_m472.glb"
python3 level_generation/creatures/claude_shared/motion_audit.py "$P/work/$RF_TAG/mm8_m472.glb" --out "$P/work/$RF_TAG/audit" > /dev/null
python3 /dev/stdin "$P/work/$RF_TAG/audit/mm8_m472.json" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))['clips']
for n in ('Standing', 'Run2'):
    print(n, {k: v['bad_pct'] for k, v in c[n]['deform'].items()}, 'pop', c[n].get('loop_pop'), 'len', c[n]['length_s'])
PY
