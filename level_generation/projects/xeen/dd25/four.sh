#!/bin/bash
# DD-25's playtests N times each (default 4), one game process at a time (exact PIDs), from ASSETS (default the scratch
# root output/studio_cal/dd25/root; the lane lead reruns with ASSETS=$PWD/assets_dev) in the Xeen world. TESTS= picks.
# Each game run goes through the session's lock and slot (flock .../a8_s13/game.lock .../a8_s9/slot.sh); LOCK=none
# skips them (a caller that already holds the lock).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd25; L=$R/devdocs/xeen/briefs/dd25/L4
ASSETS=${ASSETS:-$X/root}
LOCK=${LOCK:-$R/output/studio_cal/a8_s13/game.lock}; SLOT=$R/level_generation/projects/xeen/common/run/game_slot.sh
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_goblet playtest_hostility"}
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n
  W="flock $LOCK $SLOT"; [ "$LOCK" = none ] && W=""
  SDL_AUDIODRIVER=dummy $W "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $ASSETS --world xeen \
    --map xeen_dd25.blv --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color \
    > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E $(grep -cE '^ASSERT pass|^PASS' ${t}_$n.log) passes; $(grep -iE 'failure|FAIL' ${t}_$n.log | head -2 | cut -c1-400)"
done; done
echo "logs: $X/run/four_$S"
