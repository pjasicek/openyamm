#!/bin/bash
# four.sh: playtest.yml and playtest_hostility.yml 4 times each from the scratch root, one game at a time.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd08; L=$OYR/devdocs/xeen/briefs/xd08/L4
for n in 1 2 3 4; do for t in playtest playtest_hostility playtest_exit; do $OYR/level_generation/projects/xeen/xd08/play.sh $L/$t.yml ${t}_$n; done; done
