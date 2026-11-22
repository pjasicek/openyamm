#!/bin/bash
# play_exit.sh <log name>: the exit playtest against the combined play mount
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd06; L=$R/devdocs/xeen/briefs/xd06/L4
mkdir -p $X/run/$1.user; cd $X/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 900 $R/build/game/openyamm --asset-root "$R/output/studio_play/xeen_root" --extra-mount "$X/play_mount" --world mm7 --user-data "$X/run/$1.user" --headless-run-scenario "$L/playtest_exit.yml" --scenario-no-color > $1.log 2>&1
echo "$1 exit $? passed $(grep -c '^PASS' $1.log) of $(grep -o 'steps=[0-9]*' $1.log | head -1)"; grep -E "^(FAIL|Scenario failure)" $1.log | tail -3
