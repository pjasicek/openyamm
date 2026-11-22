#!/bin/bash
# four.sh: the playtest four times, against mount_exit (this map + X2's current mount; tools/exitmount.py)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd21; L=$R/devdocs/xeen/briefs/xd21/L4
mkdir -p $X/run/four; cd $X/run/four
for n in 1 2 3 4; do
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/output/studio_play/xeen_root --extra-mount ${MOUNT:-$X/mount_exit} --world mm7 --user-data $X/userdata/four$n --headless-run-scenario $L/${T:-playtest.yml} --scenario-no-color > run_$n.log 2>&1
  echo "run $n exit $? passed $(grep -c '^PASS' run_$n.log) of $(grep -o 'steps=[0-9]*' run_$n.log | head -1)"; grep -E "^Scenario failure" run_$n.log | tail -2
done
