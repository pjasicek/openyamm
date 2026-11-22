#!/bin/bash
# XD-18: generate, validate and build against the scratch root, install into the root, audit. Usage: cycle.sh
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd18/L4
X=$R/output/studio_cal/xd18; ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd18/gen.py >/dev/null || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $ROOT || exit 1
$O build $L --assets $ROOT --out $X/build > $X/build.log 2>&1 || { tail -15 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -3 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd18.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "xd18: build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
tail -1 $X/build.log
