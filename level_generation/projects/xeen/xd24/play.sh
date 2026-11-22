#!/bin/bash
# XD-24: one headless scenario from the scratch root (one game at a time). play.sh <scenario.yml> <name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd24; "$OYR/tools/heavy.sh" 6 BIN=$R/build-xeen/game/openyamm
mkdir -p $X/run; cd $X/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $BIN --asset-root $X/root --world xeen --headless-run-scenario $1 --scenario-no-color > $X/run/$2.log 2>&1
e=$?
echo "$2 exit $e passed $(grep -c '^PASS' $X/run/$2.log) $(grep -o 'steps=[0-9]*' $X/run/$2.log | head -1) $(grep -E '^Scenario failure|FAIL' $X/run/$2.log | head -2 | cut -c1-500)"
