#!/bin/sh
# Runs Codex masters sessions (README.md, step 2), MASTERS_JOBS (default 4) at a time.
# Usage: [MASTERS_JOBS=n] scripts/run_masters.sh [template:tier ...]
cd "$(dirname "$0")/.." || exit 1
JOBS=${*:-"w_longsword:1 w_claymore:1 w_mace:1 w_bow:1 w_longsword:2 w_claymore:2 w_mace:2 w_bow:2 w_longsword:3 w_claymore:3 w_mace:3 w_bow:3"}
for job in $JOBS; do echo "$job"; done | xargs -P "${MASTERS_JOBS:-4}" -I{} sh -c 'n=${1%:*}; t=${1#*:}; python3 -I scripts/codex_masters.py run $n $t' _ {}
