#!/bin/bash
# Build the L4, install it into the scratch mount with the no-magic overlay, and (optionally) play one test.
# Usage: go.sh [<playtest file> [<log name> [x2]]]  (x2: play in a mount with X2's current build, for the exits)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd12/L4
X=$R/output/studio_cal/xd12
A=$R/output/studio_play/xeen_root
cd $R
$O fmt $L >/dev/null
$O validate $L --assets $A | grep -v "^note: the asset root"
$O build $L --assets $A --out $X/build 2>&1 | grep -v "is named\|placeholder not built" | tail -5
$O install $L --build $X/build --mount $X/mount --assets $A >/dev/null || exit 1
[ -z "$1" ] && exit 0
mkdir -p $X/run; cd $X/run
LOG=${2:-run}.log
SC=${1}; [[ $SC = /* ]] || SC=$L/$SC
MNT=$X/mount
if [ "$3" = "x2" ]; then $OYR/level_generation/projects/xeen/xd12/mount_x2.sh >/dev/null; MNT=$X/mount_x2; fi
timeout 1800 env SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $R/build/game/openyamm --asset-root $A --extra-mount $MNT --world mm7 --user-data $X/run/userdata_$LOG --headless-run-scenario $SC --scenario-no-color > $LOG 2>&1
echo "exit $?"
grep -E "^(FAIL|Scenario failure)" $LOG | tail -5
echo "passed $(grep -c '^PASS' $LOG) of $(grep -o 'steps=[0-9]*' $LOG | head -1)"
