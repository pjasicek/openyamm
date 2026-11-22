#!/bin/bash
# XD-22: one headless playtest from the scratch root. play.sh <name> [tag]   (<name>.yml in L4, or an absolute path)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd22; L=$R/devdocs/xeen/briefs/xd22/L4
mkdir -p $X/run; cd $X/run
F=$L/$1.yml; [ -f "$1" ] && F=$1
N=$(basename $1 .yml)
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $X/root --world xeen --headless-run-scenario $F --scenario-no-color > $X/run/$N${2:-}.log 2>&1
e=$?
echo "$N exit $e passed $(grep -c '^PASS' $X/run/$N${2:-}.log) $(grep -o 'steps=[0-9]*' $X/run/$N${2:-}.log | head -1) $(grep -E '^Scenario failure|FAIL' $X/run/$N${2:-}.log | head -2 | cut -c1-500)"
