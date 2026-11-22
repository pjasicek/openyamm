#!/bin/bash
# XD-19: generate, fmt, validate, build, install into the scratch root, audit. cycle.sh [gen args]
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd19/L4
X=$R/output/studio_cal/xd19; ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd19/gen.py "$@" || exit 1
$O fmt $L >/dev/null
$O validate $L --assets $R/assets_dev > $X/validate.log 2>&1 || { tail -30 $X/validate.log; exit 1; }
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -30 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd19.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "build warnings $(grep -c '^warning' $X/build.log); audit errors $(grep -c '^error' $X/audit.txt) warnings $(grep -c '^warning' $X/audit.txt)"
