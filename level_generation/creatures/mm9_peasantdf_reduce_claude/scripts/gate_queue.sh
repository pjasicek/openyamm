#!/bin/bash
# numeric gates, installed and candidate, all four designs, one after the other
cd "$(dirname "$0")/.."
for n in 1 2 3 4; do
  scripts/gates_df.sh before/mm9_peasantdf$n.glb $n before
  scripts/gates_df.sh export/mm9_peasantdf$n.glb $n f55
done
echo QUEUE_DONE
