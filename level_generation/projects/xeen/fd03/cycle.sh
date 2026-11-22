#!/bin/bash
# FD-03: generate, validate and build against the scratch root (it holds the three new textures), install into the
# root, audit. Usage: cycle.sh
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/fd03/L4
X=$R/output/studio_cal/fd03; ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/fd03/gen.py >/dev/null || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $ROOT > $X/validate.log 2>&1 || { grep -v '^ok' $X/validate.log | head -40; exit 1; }
$O build $L --assets $ROOT --out $X/build > $X/build.log 2>&1 || { grep -E '^(error|refused)|error' $X/build.log | head -30; tail -5 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -3 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_fd03.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "fd03: build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
tail -1 $X/build.log
