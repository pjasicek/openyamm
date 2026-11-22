#!/bin/bash
# Session 19: D7 from assets_dev (walk, hostility, doors N=2), A8's DD-26 way-in test, A3's hooks_d7; one at a time.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/d7
cd $R
N=2 TESTS="playtest playtest_hostility playtest_doors" ASSETS=$R/assets_dev bash $OYR/level_generation/projects/xeen/d7/tests.sh > $X/tests_s19_ad.log 2>&1
N=2 TESTS=playtest_in ASSETS=$R/assets_dev bash $R/level_generation/projects/xeen/dd26/four.sh > $X/dd26_in_s19.log 2>&1
mkdir -p $X/xrun/hooks_s19/ud
SDL_AUDIODRIVER=dummy $R/level_generation/projects/xeen/common/run/game_slot.sh timeout 2400 $R/build-xeen/game/openyamm \
  --asset-root $R/assets_dev --world xeen --map xeen_d7.blv --user-data $X/xrun/hooks_s19/ud \
  --headless-run-scenario $R/tests/scenarios/xeen/hooks_d7.yml --scenario-no-color > $X/xrun/hooks_s19/hooks_d7.log 2>&1 &
P=$!; wait $P; echo "hooks_d7 exit $?" >> $X/xrun/hooks_s19/hooks_d7.log
echo done
