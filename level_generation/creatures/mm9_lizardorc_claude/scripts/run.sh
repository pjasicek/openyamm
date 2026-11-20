#!/bin/bash
# Usage: scripts/run.sh <script.py> args...  (Blender headless, from anywhere). Prints only the useful tail.
source /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_lizardorc_claude/scripts/env.sh
cd $REPO
s=$1; shift
out=$(tools/run_creature_blender.sh --token $TOKEN level_generation/creatures/mm9_lizardorc_claude/scripts/$s "$@" 2>&1); rc=$?
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
echo "$out" | tail -${TAIL:-12}
if [ -n "$log" ] && [ -f "$log" ]; then grep -v "^Blender\|^Read\|^Saved\|^Time:\|^ *$\|Fra:" "$log" | tail -${TAIL:-25}; fi
exit $rc
