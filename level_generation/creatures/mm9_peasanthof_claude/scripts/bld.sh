#!/bin/bash
# Like bl.sh but runs Blender directly (no workspace write lock, so it can run while a Meshy waiter polls); 12G cap,
# 4 threads; one fixed log (one Blender of this project at a time). Usage (repo root): scripts/bld.sh <grep-pattern> <script.py> [args...]
pat=$1; scr=$2; shift 2
log=level_generation/creatures/mm9_peasanthof_claude/work/blender_last.log
systemd-run --user --scope -q -p MemoryMax=${MEMMAX:-12G} -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup \
  --disable-autoexec --threads 4 --python-exit-code 1 --python "$scr" -- "$@" > "$log" 2>&1
st=$?
grep -a -E "$pat" "$log" | tail -60
if [ $st -ne 0 ]; then echo "EXIT $st"; tail -25 "$log"; fi
exit $st
