#!/bin/bash
# four.sh: playtest.yml and playtest_hostility.yml 4 times each from the scratch root, one game at a time.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd13; L=$OYR/devdocs/xeen/briefs/xd13/L4
for n in 1 2 3 4; do for t in ${TESTS:-playtest playtest_hostility}; do $OYR/level_generation/projects/xeen/xd13/play.sh $L/$t.yml ${t}_$n; done; done
