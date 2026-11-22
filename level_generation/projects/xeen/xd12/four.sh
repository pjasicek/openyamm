#!/bin/bash
# Both playtests four times each on the installed mounts (go.sh builds and installs first; playtest_b in mount_x2).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
X=$R/output/studio_cal/xd12
L=$R/devdocs/xeen/briefs/xd12/L4
A=$R/output/studio_play/xeen_root
TAG=${1:-final}
$OYR/level_generation/projects/xeen/xd12/go.sh >/dev/null
$OYR/level_generation/projects/xeen/xd12/mount_x2.sh >/dev/null
mkdir -p $X/run; cd $X/run
for t in playtest playtest_b; do
  MNT=$X/mount; [ $t = playtest_b ] && MNT=$X/mount_x2
  for n in 1 2 3 4; do
    LOG=${TAG}_${t}_$n.log
    timeout 1800 env SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $R/build/game/openyamm --asset-root $A --extra-mount $MNT --world mm7 --user-data $X/run/ud_${TAG}_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > $LOG 2>&1
    echo "$t run $n exit $? passed $(grep -c '^PASS' $LOG) of $(grep -o 'steps=[0-9]*' $LOG | head -1) $(grep -E '^Scenario failure' $LOG | head -1)"
  done
done > $X/run/${TAG}_four.out
cat $X/run/${TAG}_four.out
