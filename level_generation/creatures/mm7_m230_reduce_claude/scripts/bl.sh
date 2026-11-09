#!/usr/bin/env bash
# Run one of this project's Blender scripts through the lease wrapper and print its log.
# Usage: TOKEN=<lease> scripts/bl.sh <script.py> [args...]
set -uo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"
s=$1; shift
out=$("$ROOT/tools/run_creature_blender.sh" --token "${TOKEN:?set TOKEN}" "level_generation/creatures/$(basename "$P")/scripts/$s" "$@" 2>&1); rc=$?
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
[ -n "$log" ] && cat "$log" || echo "$out"
exit $rc
