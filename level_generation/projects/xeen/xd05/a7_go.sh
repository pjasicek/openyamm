#!/bin/bash
# Lane A7: regenerate, fmt, validate, build against assets_dev (studio merge point 3 reads the Xeen world's rows),
# install into assets_dev (map files only), audit --reach --solve, dressing check, fmt --check.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
R=$OYR; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd05/L4
X=$R/output/studio_cal/xd05; cd $R
python3 $OYR/level_generation/projects/xeen/xd05/history/tools/gen.py >/dev/null && $O fmt $L >/dev/null
$O validate $L --assets assets_dev || exit 1
$O build $L --assets assets_dev --out $X/a7_xbuild > $X/a7_xbuild.log 2>&1; echo "build exit $? ($(grep -c warning $X/a7_xbuild.log) warnings)"
$O install $L --build $X/a7_xbuild --root assets_dev | tail -1
$O audit assets_dev/worlds/xeen/maps/xeen_xd05.blv --world xeen --assets assets_dev --reach --solve > $X/a7_xaudit.txt 2>&1; echo "audit exit $?"
$O export $X/a7_xbuild/xeen_xd05.blv --out $X/a7_export.json >/dev/null 2>&1
python3 $R/output/studio_cal/a7/dressing/check_dressing.py $L $X/a7_export.json | head -1
$O fmt $L --check; echo "fmt check exit $?"
