#!/bin/bash
# four.sh: the L4 playtests 4 times each from the scratch root, one game at a time.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd24; L=$OYR/devdocs/xeen/briefs/xd24/L4
for n in 1 2 3 4; do for t in ${TESTS:-playtest playtest_hostility playtest_exit}; do $OYR/level_generation/projects/xeen/xd24/play.sh $L/$t.yml ${t}_$n; done; done
