#!/bin/bash
# the four playtests four times each, one game at a time (play.sh waits on PIDs); from assets_dev, no mount
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd09
N=${1:-4}
$OYR/level_generation/projects/xeen/xd09/play.sh playtest.yml main $N
$OYR/level_generation/projects/xeen/xd09/play.sh playtest_hostility.yml host $N
$OYR/level_generation/projects/xeen/xd09/play.sh playtest_exit.yml exit $N
$OYR/level_generation/projects/xeen/xd09/play.sh playtest_in.yml in $N none
