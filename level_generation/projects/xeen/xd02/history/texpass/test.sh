#!/bin/bash
# Texture pass: fmt, validate, build, install into mount/, then the playtest four times (logs in run2/).
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd02/L4
X=$R/output/studio_cal/xd02
cd $R
$O fmt $L >/dev/null
$O validate $L --assets assets_dev || exit 1
$O build $L --assets assets_dev --out $X/build 2>&1 | grep -v "is named" | tail -3
$O install $L --build $X/build --mount $X/mount --assets assets_dev >/dev/null || exit 1
mkdir -p $X/run2; cd $X/run2
for n in 1 2 3 4; do
  timeout 1500 $R/build/game/openyamm --asset-root $R/assets_dev --extra-mount $X/mount --world mm7 --headless-run-scenario $L/playtest.yml --scenario-no-color > final_$n.log 2>&1
  echo "run $n exit $? passed $(grep -c '^PASS' final_$n.log) of $(grep -o 'steps=[0-9]*' final_$n.log | head -1) $(grep -E '^Scenario failure' final_$n.log | head -1)"
done > four.out
cat four.out
