#!/bin/bash
# Read-only review renders (write only under review/): Blender headless without the lease lock, under the 12G cap. Usage (repo root): scripts/blr.sh <script.py> [args...]
s=$1; shift
L=/tmp/claude-1000/pf4_blr_last.log
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python "$s" -- "$@" > $L 2>&1
st=$?; [ $st -ne 0 ] && { grep -A12 Traceback $L | tail -14; echo "EXIT $st"; }; exit $st
