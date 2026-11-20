#!/bin/sh
# prep.py layouts of the named templates, in parallel (README.md, Route 1). Usage: scripts/run_prep.sh <template>...
cd "$(dirname "$0")/.." || exit 1
for n in "$@"; do
  ( blender --background --python scripts/prep.py -- $n 4 > work/prep_$n.log 2>&1; echo "$n exit $?" >> work/prep_done.txt ) &
done
wait
