#!/bin/bash
# XD-22: regenerate L4, fmt, validate, build, install into the scratch root, audit --reach --solve (agent:xeen-a7-xd22)
# GEN_ARGS=--standin uses the shipped stand-in (t2bedsht) for the two new paper textures.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd22/L4; X=$R/output/studio_cal/xd22
ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd22/gen.py $GEN_ARGS || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $ROOT || exit 1
$O build $L --assets $ROOT --out $X/build > $X/build.log 2>&1 || { tail -25 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd22.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
$O fmt --check $L > /dev/null 2>&1 && echo "fmt clean" || echo "fmt NOT clean"
echo "build warnings $(grep -c '^warning' $X/build.log); $(tail -1 $X/build.log)"; grep '^warning' $X/build.log | cut -c1-300
echo "audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-300
