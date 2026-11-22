#!/bin/bash
# Pass 2: the playtest on this pass's private root, $1 runs at once in parallel (default 4), logs in run/<tag>/.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
X=$R/output/studio_cal/xd02/pass2
L=$R/devdocs/xeen/briefs/xd02/L4
N=${1:-4}; TAG=${2:-four}
mkdir -p $X/run/$TAG; cd $X/run/$TAG
for n in $(seq 1 $N); do
  ( timeout 1500 $R/build/game/openyamm --asset-root $X/root --world mm7 --headless-run-scenario $L/playtest.yml --scenario-no-color > playtest_$n.log 2>&1
    echo "playtest run $n exit $? passed $(grep -c '^PASS' playtest_$n.log) of $(grep -o 'steps=[0-9]*' playtest_$n.log | head -1) $(grep -E '^Scenario failure' playtest_$n.log | head -1)" ) &
done
wait
