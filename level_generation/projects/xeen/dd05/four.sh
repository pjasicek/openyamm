#!/bin/bash
# DD-05's playtests N times each (default 4), one game process at a time (exact PIDs), from ASSETS (default the scratch
# root output/studio_cal/dd05/root; the lane lead reruns with ASSETS=$PWD/assets_dev) in the Xeen world. TESTS= picks.
# Each run keeps its user-data folder ud_<test>_<n> beside its log (delete the run folder when done).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd05; L=$R/devdocs/xeen/briefs/dd05/L4
ASSETS=${ASSETS:-$X/root_s9}
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_hostility playtest_exit"}
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $ASSETS --world xeen --map xeen_dd05.blv \
    --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E steps $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -cE '^PASS' ${t}_$n.log) PASS; $(grep -iE 'failure|FAIL' ${t}_$n.log | head -2 | cut -c1-400)"
done; done
echo "logs: $X/run/four_$S"
