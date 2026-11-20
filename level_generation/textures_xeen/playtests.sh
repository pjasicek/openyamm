#!/bin/bash
# The three dungeons' playtests, four runs each, against one asset root: playtests.sh <root> <log dir>
R=/home/pjasicek/github/OpenYAMM
ROOT=$1; OUT=$2
mkdir -p $OUT; cd $OUT
run() {
  local key=$1 test=$2 n=$3
  local log=$OUT/${key}_${test}_$n.log
  timeout 1500 $R/build/game/openyamm --asset-root $ROOT --world mm7 --headless-run-scenario $R/devdocs/xeen/briefs/$key/L4/$test.yml --scenario-no-color > $log 2>&1
  echo "$key $test run $n exit $? passed $(grep -c '^PASS' $log) of $(grep -o 'steps=[0-9]*' $log | head -1) $(grep -E '^Scenario failure' $log | head -1)"
}
for n in 1 2 3 4; do
  for kt in xd01:playtest xd01:playtest_perception xd02:playtest xd03:playtest xd03:playtest_alarm; do
    run ${kt%%:*} ${kt##*:} $n &
  done
  wait
done
