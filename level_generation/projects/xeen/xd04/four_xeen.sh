#!/bin/bash
# Pass five (X1's tower door moved north): XD-04's two playtests four times each against output/studio_play/xeen_root.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
X=$R/output/studio_cal/xd04
L=$R/devdocs/xeen/briefs/xd04/L4
mkdir -p $X/run; cd $X/run
for t in playtest playtest_m4; do
for n in 1 2 3 4; do
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/output/studio_play/xeen_root --world mm7 --headless-run-scenario $L/$t.yml --scenario-no-color > p5_${t}_$n.log 2>&1
  echo "$t run $n exit $? passed $(grep -c '^PASS' p5_${t}_$n.log) of $(grep -o 'steps=[0-9]*' p5_${t}_$n.log | head -1) $(grep -E '^Scenario failure' p5_${t}_$n.log | head -1)"
done; done > p5_four.out
cat p5_four.out
