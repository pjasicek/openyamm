#!/usr/bin/env bash
# Run one project Blender step under the lease: TOK=<lease> scripts/run.sh <script.py> [args...]; prints the step's
# upper-case report lines and any traceback.
set -uo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$repo"
out=$(tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/hes_custodian_claude/scripts/$1" "${@:2}" 2>&1)
log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
[ -n "$log" ] || { echo "$out"; exit 1; }
grep -E "^[A-Z][A-Z0-9_]+ " "$log" | grep -v -E "^(Blender|Read|Info|INFO|Fra|Saved|FBX)" | cut -c1-400
if grep -q "Traceback\|Error:" "$log"; then grep -B2 -A14 "Traceback\|Error:" "$log" | head -40; echo "STEP FAILED $1"; exit 1; fi
