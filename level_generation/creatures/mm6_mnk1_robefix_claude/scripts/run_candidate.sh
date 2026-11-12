#!/usr/bin/env bash
# One BMonk Run2 candidate (robefix 2026-11-12), from the repository root:
#   RF_TAG=<tag> RF_RUN='<json cfg over the 2026-10-21 Run2 cfg>' scripts/run_candidate.sh <token>
# Blender (one at a time): gait2_author (Run2 only) -> gait2_export; graft over the installed GLB backup
# (work/before_robefix/mm6_mnk1.glb) -> work/<tag>/mm6_mnk1.glb; motion audit -> work/<tag>/audit/.
set -euo pipefail
P=level_generation/creatures/mm6_mnk1_robefix_claude
TOKEN=$1
: "${RF_HEM:={}}"
export RF_TAG RF_RUN RF_HEM
mkdir -p "$P/work/$RF_TAG"
for s in gait2_author gait2_export; do
    out=$(tools/run_creature_blender.sh --token "$TOKEN" "$P/scripts/$s.py" 2>&1 || true)
    log=$(printf '%s\n' "$out" | sed -n 's/^Blender log: //p')
    cp "$log" "$P/work/$RF_TAG/$s.log"
    if grep -q Traceback "$log"; then grep -A30 Traceback "$log" | tail -30; exit 1; fi
    grep -E "^GAIT2 |CLOTH_FLOOR|GAIT2_EXPORTED" "$log" | cut -c1-400 | tail -4 || true
done
python3 "$P/scripts/gait2_graft.py" "$P/work/before_robefix/mm6_mnk1.glb" "$P/work/$RF_TAG/mm6_mnk1.glb"
python3 level_generation/creatures/claude_shared/motion_audit.py "$P/work/$RF_TAG/mm6_mnk1.glb" --out "$P/work/$RF_TAG/audit" > /dev/null
python3 /dev/stdin "$P/work/$RF_TAG/audit/mm6_mnk1.json" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))['clips']
for n in ('Standing', 'Run2'):
    print(n, {k: v['bad_pct'] for k, v in c[n]['deform'].items()}, 'pop', c[n].get('loop_pop'), 'len', c[n]['length_s'])
PY
python3 level_generation/creatures/mm8_m472_robefix_claude/scripts/stride_of.py "$P/work/$RF_TAG/mm6_mnk1.glb" Run2
