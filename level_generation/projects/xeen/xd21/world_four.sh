#!/bin/bash
# the three playtests four times each from assets_dev in the Xeen world, one game at a time (world_play.sh waits on PIDs)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd21
$OYR/level_generation/projects/xeen/xd21/world_play.sh playtest.yml main 4
$OYR/level_generation/projects/xeen/xd21/world_play.sh playtest_hostility.yml host 4
$OYR/level_generation/projects/xeen/xd21/world_play.sh playtest_way_in.yml wayin 4 none
