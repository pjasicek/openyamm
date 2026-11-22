#!/bin/bash
# XD-22: each playtest 4 times from the scratch root, one game at a time (logs run/<name>_<n>.log).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd22
for n in 1 2 3 4; do for t in playtest playtest_hostility playtest_exit; do $OYR/level_generation/projects/xeen/xd22/play.sh $t _$n; done; done
