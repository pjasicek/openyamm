#!/bin/bash
# Read-only review renders (writes only under review/): Blender headless without the lease lock; log overwritten each run.
# Usage: scripts/blr.sh <script.py> [args...]   (repo root)
s=$1; shift
L=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/74ae08a0-ce66-4dda-8cb9-a8062f5327d4/scratchpad/blr_last.log
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python "$s" -- "$@" > $L 2>&1
st=$?; [ $st -ne 0 ] && { grep -A12 Traceback $L | tail -14; echo "EXIT $st"; }
grep -E "^[A-Z_]{4,} " $L | tail -20; exit $st
