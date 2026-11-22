#!/bin/bash
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; A=$R/output/studio_play/xeen_root; D=$R/output/studio_cal/xd01/final; P=$R/devdocs/xeen/briefs/xd01/L4
mkdir -p $D
run() { mkdir -p $D/$2_$3; (cd $D/$2_$3 && SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1800 $R/build/game/openyamm --asset-root $A --world mm7 --headless-run-scenario $P/$1.yml --scenario-no-color > log.txt 2>&1); echo "$2 $3 rc=$? $(grep -E '^Scenario (passed|failure)' $D/$2_$3/log.txt | cut -c1-200)"; }
for i in 1 2 3 4; do run playtest walk $i & run playtest walk $((i+4)) & run playtest_perception perc $i & wait; done
