#!/bin/bash
# XD-14: generate, fmt, validate, build, install into the scratch root, audit (--reach --solve).
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd14/L4
X=$R/output/studio_cal/xd14; ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd14/gen.py || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev > $X/validate.log 2>&1 || { cat $X/validate.log | head -40; exit 1; }
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { grep -v "^warning" $X/build.log | tail -30; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd14.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
