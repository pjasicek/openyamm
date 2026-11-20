#!/usr/bin/env bash
# One Blender at a time for this agent (work/blender.lock), memory-capped, through the creature wrapper with this lease.
# Usage (any folder): scripts/bl.sh <log file> <script.py relative to the repo> [args...]
set -u
R=/home/pjasicek/github/OpenYAMM; P=$R/level_generation/creatures/mm9_sven_lining_claude
log=$1; shift; T=$(cat $P/LEASE_TOKEN.txt)
cd $R && flock $P/work/blender.lock systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 \
  tools/run_creature_blender.sh --token $T "$@" > "$log" 2>&1
rc=$?; bl=$(grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' "$log" | head -1)
[[ -n "$bl" ]] && cat "$bl" >> "$log"
echo "BL rc=$rc log=$log"
