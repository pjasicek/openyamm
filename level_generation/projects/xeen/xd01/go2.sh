#!/bin/bash
# Second pass: build, install into the mount, run one playtest headless. Usage: go2.sh <playtest file name> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
set -e
R=$OYR
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd01/L4
X=$R/output/studio_cal/xd01
cd $R
$O fmt $L >/dev/null
$O validate $L --assets assets_dev
$O build $L --assets assets_dev --out $X/build 2>&1 | grep -v "is named" || true
$O install $L --build $X/build --mount $X/mount --assets assets_dev >/dev/null
mkdir -p $X/run2; cd $X/run2
LOG=${2:-run}.log
set +e
"$OYR/tools/heavy.sh" 6 timeout 1200 $R/build/game/openyamm --asset-root $R/assets_dev --extra-mount $X/mount --world mm7 --headless-run-scenario $L/${1:-playtest.yml} --scenario-no-color > $LOG 2>&1
echo "exit $?"
grep -E "^(FAIL|Scenario failure)" $LOG | tail -5
echo "passed $(grep -c '^PASS' $LOG) of $(grep -o 'steps=[0-9]*' $LOG | head -1)"
