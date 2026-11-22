#!/bin/bash
# Pass 2: the two playtests on this pass's root, $1 runs each (default 4), logs in run/<tag>/.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
X=$R/output/studio_cal/xd03/pass2
L=$R/devdocs/xeen/briefs/xd03/L4
N=${1:-4}; TAG=${2:-four}; ROOT=${3:-$X/root}
mkdir -p $X/run/$TAG; cd $X/run/$TAG
for n in $(seq 1 $N); do
  for t in playtest playtest_alarm; do
    ( timeout 1500 $R/build/game/openyamm --asset-root $ROOT --world mm7 --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1
      echo "$t run $n exit $? passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1)" ) &
  done
  wait
done > $X/run/$TAG/result.out
cat $X/run/$TAG/result.out
