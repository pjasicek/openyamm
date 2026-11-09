#!/usr/bin/env bash
# Run one project Blender script through tools/run_creature_blender.sh and print the lines of ITS log matching $PAT
# (other sessions write logs at the same time, so the newest log is not necessarily ours). TOKEN = workspace lease.
# Usage: PAT='^(CARRY|TWIST)' scripts/b.sh <script.py> [args...]
set -uo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
cd "$P/../../.."
s=$1; shift
out=$("$P/scripts/cap.sh" tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$(basename "$P")/scripts/$s" "$@" 2>&1)
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
if [ -z "$log" ]; then echo "$out" | tail -5; exit 1; fi
if grep -q "Error: script failed\|Traceback" "$log"; then grep -E "${PAT:-^[A-Z0-9]+ }" "$log" | cut -c1-260; grep -A14 Traceback "$log" | tail -16; echo "STEP FAILED: $s ($log)"; exit 1; fi
grep -E "${PAT:-^[A-Z0-9]+ }" "$log" | cut -c1-260
