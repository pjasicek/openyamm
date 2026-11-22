#!/bin/bash
# Both playtests against an asset root, n runs each in parallel pairs: play.sh <root> <log dir> <runs>
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
ROOT=$1; OUT=$2; N=${3:-1}
mkdir -p $OUT; cd $OUT
run() {
  local test=$1 n=$2
  local log=$OUT/${test}_$n.log
  timeout 1500 $R/build/game/openyamm --asset-root $ROOT --world mm7 --headless-run-scenario $R/devdocs/xeen/briefs/xd04/L4/$test.yml --scenario-no-color > $log 2>&1
  echo "$test run $n exit $? passed $(grep -c '^PASS' $log) of $(grep -o 'steps=[0-9]*' $log | head -1) $(grep -E '^Scenario failure' $log | head -1)"
}
for n in $(seq 1 $N); do
  run playtest $n &
  run playtest_m4 $n &
  wait
done
