#!/usr/bin/env bash
# Run one Blender step of this project under the lease and print its own log's result lines.
# Usage: TOK=<lease> scripts/step.sh <script.py> [args...]
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$(basename "$here")/scripts/$1" "${@:2}" 2>&1)
log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO|Warning|WARNING)' | cut -c1-400
if grep -q "Traceback\|script failed" "$log"; then grep -A14 Traceback "$log" | head -24; echo "STEP FAILED: $1 ($log)"; exit 1; fi
