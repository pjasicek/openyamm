#!/bin/bash
# A6: the final checks in a row against assets_dev (one game process at a time under the lane's game2 lock): walk
# twice, hostility, then the gates tour (tour_only.sh, no install).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
cd "$OYR"
W=level_generation/projects/xeen/d2/walk.sh
L=output/studio_cal/a6/locks/game2.lock
P=$OYR/devdocs/xeen/briefs/d2/L4
flock $L $W $P/playtest.yml walk_i1.log
flock $L $W $P/playtest.yml walk_i2.log
flock $L $W $P/playtest_hostility.yml host_i1.log
flock $L level_generation/projects/xeen/d2/tour_only.sh gates gates
echo finished > output/studio_cal/d2/run/final_tests_i.done
