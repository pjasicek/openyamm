#!/bin/bash
# build, install into the mount, play one test: go.sh <playtest.yml> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; O=$R/openyamm-studio/build/oymap; L=$R/devdocs/xeen/briefs/xd27/L4; X=$R/output/studio_cal/xd27
cd $R; $O fmt $L >/dev/null
$O build $L --assets $R/output/studio_play/xeen_root --mount $X/mount --out $X/build 2>&1 | grep -v "is named\|placeholder not built" | tail -4
$O install $L --build $X/build --mount $X/mount --assets $R/output/studio_play/xeen_root >/dev/null; python3 $OYR/level_generation/projects/xeen/xd27/play_mount.py >/dev/null
mkdir -p $X/run/ud_$2; cd $X/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/output/studio_play/xeen_root --extra-mount $X/${MOUNT:-mount_play} --world mm7 --user-data $X/run/ud_$2 --headless-run-scenario $L/$1 --scenario-no-color > $2.log 2>&1
echo "exit $? passed $(grep -c '^PASS' $2.log) of $(grep -o 'steps=[0-9]*' $2.log | head -1)"; grep -E "^(FAIL|Scenario failure)" $2.log | tail -5
