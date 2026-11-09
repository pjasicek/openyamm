#!/bin/bash
# Run a Blender script of this project under the lease and print the log's matching lines.
# Usage: scripts/bl.sh <grep-pattern> <script.py> [args...]   (from the repo root)
pat=$1; shift
out=$(CREATURE_3D_TOKEN=$(cat level_generation/creatures/mm9_peasantm7d_claude/LEASE_TOKEN.txt) tools/run_creature_blender.sh "$@" 2>&1)
st=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
echo "$out" | grep -v '^Blender log'
[ -n "$log" ] && grep -a -E "$pat" "$log" | tail -60
if [ $st -ne 0 ] || grep -q Traceback "$log" 2>/dev/null; then echo "EXIT $st"; [ -n "$log" ] && grep -a -A15 Traceback "$log" | tail -25; fi
exit $st
