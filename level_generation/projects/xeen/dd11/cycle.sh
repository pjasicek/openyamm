#!/bin/bash
# DD-11A/B/C: regenerate, fmt, validate, build, install into the shared scratch root, audit --reach --solve.
# cycle.sh <key>   (dd11a, dd11b, dd11c; agent:xeen-a7-dd11)
K=$1
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/$K/L4; X=$R/output/studio_cal/$K
ROOT=$R/output/studio_cal/dd11/root
cd $R
python3 level_generation/projects/xeen/dd11/gen.py || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev > $X/validate.log 2>&1 || { cat $X/validate.log | head -40; exit 1; }
grep -v '^ok' $X/validate.log | head -20
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -25 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_$K.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
$O fmt --check $L > /dev/null 2>&1 && echo "fmt clean" || echo "fmt NOT clean"
echo "build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-300
