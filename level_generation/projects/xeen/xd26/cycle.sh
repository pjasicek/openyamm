#!/bin/bash
# XD-26: regenerate, fmt, validate, build, install into the scratch root, audit --reach --solve (agent:xeen-a7-xd26)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd26/L4; X=$R/output/studio_cal/xd26
ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd26/gen.py || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $ROOT || exit 1
$O build $L --assets $ROOT --out $X/build > $X/build.log 2>&1 || { tail -5 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd26.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
$O fmt --check $L > /dev/null 2>&1 && echo "fmt clean" || echo "fmt NOT clean"
echo "build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
