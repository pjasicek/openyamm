#!/bin/bash
# Build, install into the mount and run one playtest headless. Usage: go.sh [<playtest file>] [<log name>]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
set -e
R=$OYR
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd04/L4
X=$R/output/studio_cal/xd04
cd $R
$O fmt $L >/dev/null
$O validate $L --assets assets_dev
$O build $L --assets assets_dev --out $X/build 2>&1 | grep -v "is named\|placeholder not built" || true
$O install $L --build $X/build --mount $X/mount --assets assets_dev >/dev/null
mkdir -p $X/run; cd $X/run
LOG=${2:-run}.log
SC=${1:-playtest.yml}; [[ $SC = /* ]] || SC=$L/$SC
set +e
"$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/assets_dev --extra-mount $X/mount --world mm7 --headless-run-scenario $SC --scenario-no-color > $LOG 2>&1
echo "exit $?"
grep -E "^(FAIL|Scenario failure)" $LOG | tail -5
echo "passed $(grep -c '^PASS' $LOG) of $(grep -o 'steps=[0-9]*' $LOG | head -1)"
