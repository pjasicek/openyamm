#!/bin/bash
# DD-13: every playtest four times from the scratch root, one game at a time.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/dd13
: > $X/four.out
for i in 1 2 3 4; do
  for t in playtest playtest_peace playtest_hostility playtest_exit; do
    echo "dd13 $t run $i $($OYR/level_generation/projects/xeen/dd13/play.sh $t _r$i)" >> $X/four.out
  done
done
echo finished >> $X/four.out
