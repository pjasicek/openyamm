#!/bin/bash
# DD-24: generate, validate and build against the scratch root (it holds the two new textures), install into the
# root, audit. Usage: cycle.sh
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/dd24/L4
X=$R/output/studio_cal/dd24; ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/dd24/gen.py >/dev/null || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $ROOT || exit 1
$O build $L --assets $ROOT --out $X/build > $X/build.log 2>&1 || { tail -5 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -3 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_dd24.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "dd24: build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
tail -1 $X/build.log
