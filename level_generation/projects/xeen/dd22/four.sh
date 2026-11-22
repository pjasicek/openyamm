#!/bin/bash
# DD-22's playtests N times each (default 4), one game process at a time (exact PIDs), from ASSETS (default the scratch
# root output/studio_cal/dd22/root; the lane lead reruns with ASSETS=$PWD/assets_dev) in the Xeen world. TESTS= picks.
# Each run keeps its user-data folder ud_<test>_<n> beside its log (delete the run folder when done).
# Every game run goes through the session's lock (LOCK= empty to skip it).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd22; L=$R/devdocs/xeen/briefs/dd22/L4
ASSETS=${ASSETS:-$X/root}
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_exit playtest_hostility playtest_in"}
LOCK=${LOCK-$R/output/studio_cal/a8_s14/game.lock}
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n
  f=$L/$t.yml; [ -f "$f" ] || f=$X/explore/$t.yml
  if [ -n "$LOCK" ]; then W=(flock $LOCK); else W=(); fi
  SDL_AUDIODRIVER=dummy "${W[@]}" "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $ASSETS --world xeen \
    --map xeen_dd22.blv --user-data $PWD/ud_${t}_$n --headless-run-scenario $f --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E $(grep -cE '^ASSERT pass|^PASS' ${t}_$n.log) passes; $(grep -iE 'failure|FAIL' ${t}_$n.log | head -2 | cut -c1-400)"
done; done
echo "logs: $X/run/four_$S"
