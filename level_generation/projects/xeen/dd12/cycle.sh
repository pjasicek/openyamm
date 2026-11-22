#!/bin/bash
# DD-12: generate, fmt, validate, build, install into the scratch root, audit. cycle.sh [L4]
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; X=$R/output/studio_cal/dd12
LV=${1:-L4}; L=$R/devdocs/xeen/briefs/dd12/$LV; ROOT=${ROOT:-$X/root}
cd $R
python3 level_generation/projects/xeen/dd12/gen.py $LV || exit 1
$O fmt $L >/dev/null
$O validate $L --assets $R/assets_dev 2>&1 | grep -v "^note: the asset root" ; [ ${PIPESTATUS[0]} = 0 ] || exit 1
[ $LV = L1 -o $LV = L2 ] && exit 0
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -20 $X/build.log; exit 1; }
echo "build: $(grep -c '^warning' $X/build.log) warnings"; grep -E "^(warning|error)" $X/build.log | cut -c1-260
[ $LV = L3 ] && exit 0
for f in $ROOT/worlds/xeen/maps/xeen_dd12.blv $ROOT/worlds/xeen/maps/xeen_dd12.scene.yml $ROOT/worlds/xeen/events/maps/xeen_dd12.lua; do
  [ -e $f ] && [ "$(stat -c %h $f)" != 1 ] && { echo "LINKED: $f"; exit 1; }
done
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_dd12.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
$O record $L --author agent:xeen-a8-dd12 --label "${2:-generator run}" >/dev/null
