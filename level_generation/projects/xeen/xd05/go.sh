#!/bin/bash
# build, install into the private root, play one test: go.sh <playtest> <log>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; O=$R/openyamm-studio/build/oymap; L=$R/devdocs/xeen/briefs/xd05/L4; X=$R/output/studio_cal/xd05
cd $R; $O fmt $L >/dev/null
$O build $L --assets $X/root --out $X/build 2>&1 | grep -v "is named\|placeholder not built\|gate_bar rises" | tail -3
$O install $L --build $X/build --root $X/root >/dev/null
mkdir -p $X/run; cd $X/run
"$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $X/root --world mm7 --headless-run-scenario $L/$1 --scenario-no-color > $2.log 2>&1
echo "exit $? passed $(grep -c '^PASS' $2.log) of $(grep -o 'steps=[0-9]*' $2.log | head -1)"; grep -E "^(FAIL|Scenario failure)" $2.log | tail -3
