#!/usr/bin/env bash
# Run one project Blender script through the creature wrapper (lease token in REA_TOKEN) and print the lines of its
# log that match REA_GREP (default: upper-case result tags, errors). Usage: scripts/b.sh <script.py> [args...]
set -uo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
s=$1; shift
out=$("$repo/tools/run_creature_blender.sh" --token "${REA_TOKEN:?}" level_generation/creatures/mm7_m266_reduce_claude/scripts/$s "$@" 2>&1); rc=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
[ -n "$log" ] && grep -E "${REA_GREP:-^[A-Z][A-Z_0-9]+ |Error|Traceback|line [0-9]+}" "$log" | cut -c1-400
[ $rc -ne 0 ] && { echo "$out" | tail -5; echo "FAILED rc=$rc log $log"; }
exit $rc
