#!/bin/bash
# DD-11A/B/C: one headless playtest from the shared scratch root. play.sh <key> <name> [tag]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
K=$1; N=$2; T=${3:-}
R=$OYR; X=$R/output/studio_cal/$K; L=$R/devdocs/xeen/briefs/$K/L4
mkdir -p $X/run; cd $X/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $R/output/studio_cal/dd11/root --world xeen --headless-run-scenario $L/$N.yml --scenario-no-color > $X/run/$N$T.log 2>&1
e=$?
echo "$K $N$T exit $e passed $(grep -c '^PASS' $X/run/$N$T.log) $(grep -o 'steps=[0-9]*' $X/run/$N$T.log | head -1) $(grep -E '^Scenario failure|FAIL' $X/run/$N$T.log | head -2 | cut -c1-400)"
