#!/bin/bash
# play.sh <playtest.yml> <log name>: one headless run against the scratch mount
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd06; L=$R/devdocs/xeen/briefs/xd06/L4
mkdir -p $X/run/$2.user; cd $X/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root "$R/output/studio_play/xeen_root" --extra-mount "$X/mount" --world mm7 --user-data "$X/run/$2.user" --headless-run-scenario "$L/$1" --scenario-no-color > $2.log 2>&1
echo "$2 exit $? passed $(grep -c '^PASS' $2.log) of $(grep -o 'steps=[0-9]*' $2.log | head -1)"; grep -E "^(FAIL|Scenario failure)" $2.log | tail -3
