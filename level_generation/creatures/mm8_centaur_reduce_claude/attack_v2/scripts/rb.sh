#!/usr/bin/env bash
# Run a m532 Blender script through the creature wrapper and print its own log (no "latest log" guessing).
# Usage: rb.sh <script.py relative to the repo> [args...]
cd /home/pjasicek/github/OpenYAMM
out=$(tools/run_creature_blender.sh --token 14b95059ace240109fd13d1eddbb6d76 "$@" 2>&1); rc=$?
log=$(printf '%s\n' "$out" | sed -n 's/^Blender log: //p' | head -1)
printf '%s\n' "$out" | grep -v '^Blender log: '
[[ -n $log ]] && { cat "$log"; rm -f "$log"; }
exit $rc
