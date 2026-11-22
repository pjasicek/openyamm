#!/bin/bash
# The playtests N times each (default 4), one game process at a time, from assets_dev with the Xeen world, --map xeen_xd11.blv.
# A2 wrote row 9127 (2026-11-20) and the test mount was deleted; MOUNT=1 would add output/studio_cal/xd11/mount (gone; copies of the world's map_stats.txt and
# bolster_maps.txt with the row) as --extra-mount.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd11; L=$R/devdocs/xeen/briefs/xd11/L4
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_hostility playtest_exit playtest_exit_x3 playtest_in"}
EXTRA=; [ "${MOUNT:-0}" = 1 ] && EXTRA="--extra-mount $X/mount"
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n; MAPARG="--map xeen_xd11.blv"; [ $t = playtest_in ] && MAPARG=
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $R/assets_dev $EXTRA --world xeen $MAPARG \
    --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-300)"
done; done
echo "logs: $X/run/four_$S"
