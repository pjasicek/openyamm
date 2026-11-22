#!/bin/bash
# DD-06: one headless playtest from the scratch root. play.sh <name> [tag]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd06; L=$R/devdocs/xeen/briefs/dd06/L4
mkdir -p $X/run; cd $X/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $X/root --world xeen --headless-run-scenario $L/$1.yml --scenario-no-color > $X/run/$1${2:-}.log 2>&1
e=$?
echo "$1 exit $e passed $(grep -c '^PASS' $X/run/$1${2:-}.log) $(grep -o 'steps=[0-9]*' $X/run/$1${2:-}.log | head -1) $(grep -E '^Scenario failure|FAIL' $X/run/$1${2:-}.log | head -2 | cut -c1-400)"
