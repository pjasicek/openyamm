#!/bin/bash
# DD-06: regenerate, fmt, validate, build, install into the scratch root, audit --reach --solve (agent:xeen-a7-dd06)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/dd06/L4; X=$R/output/studio_cal/dd06
ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/dd06/gen.py || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev > $X/validate.log 2>&1 || { tail -30 $X/validate.log; exit 1; }
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -30 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_dd06.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
$O fmt --check $L > /dev/null 2>&1 && echo "fmt clean" || echo "fmt NOT clean"
echo "build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
