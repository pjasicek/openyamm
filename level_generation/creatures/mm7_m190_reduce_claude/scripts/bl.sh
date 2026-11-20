#!/usr/bin/env bash
# Run one of this project's Blender scripts under the creature lease and print its log lines matching BL_GREP
# (default: tracebacks and errors). Usage: TOKEN=<lease> BL_GREP='REGION|region' bl.sh <script.py> [args...]
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../../../.." && pwd); s=$1; shift
out=$("$ROOT/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m190_reduce_claude/scripts/$s" "$@" 2>&1)
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
[ -n "$log" ] || { echo "$out"; exit 1; }
grep -E "${BL_GREP:-Traceback|Error:}|Traceback|Error:" "$log"; echo "LOG $log"
