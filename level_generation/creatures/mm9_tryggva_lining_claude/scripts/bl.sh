#!/usr/bin/env bash
# One Blender job of this project under the memory cap and the project lease, one at a time (work/blender.lock).
# Usage (any folder): scripts/bl.sh <grep pattern for the log> <script path relative to the repo> [args ...]
set -u
R=/home/pjasicek/github/OpenYAMM; P=$R/level_generation/creatures/mm9_tryggva_lining_claude
pat=$1; shift
cd $R
out=$(flock $P/work/blender.lock systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 \
  tools/run_creature_blender.sh --token "$(cat $P/LEASE_TOKEN.txt)" "$@" 2>&1); rc=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
echo "$out" | grep -v '^Blender log' | head -5
[[ -n $log ]] && grep -a -E "$pat" "$log"
echo "BL rc=$rc log=$log"
exit $rc
