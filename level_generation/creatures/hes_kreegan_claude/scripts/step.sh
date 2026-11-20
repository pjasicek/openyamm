#!/usr/bin/env bash
# One Blender step under the lease: scripts/step.sh <script.py> [args...]; prints the script's own report lines.
cd "$(dirname "$0")/.."
P=$PWD; NAME=$(basename "$P"); REPO=$(cd ../../.. && pwd)
: "${TOK:?set TOK to the workspace lease token}"
out=$(cd "$REPO" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$NAME/scripts/$1" "${@:2}" 2>&1) || true
log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO|Warning|WARN)' | cut -c1-300 || true
if grep -q "Traceback\|script failed" "$log"; then grep -A14 Traceback "$log" | head -24; echo "STEP FAILED: $1 ($log)"; exit 1; fi
