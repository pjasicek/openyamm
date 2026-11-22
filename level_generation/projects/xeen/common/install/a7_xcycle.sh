#!/bin/bash
# Lane A7: fmt, validate, build to output/studio_cal/<key>/a7_xbuild, audit (--reach --solve) the built map. xcycle.sh xd02
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; k=$1; L=$R/devdocs/xeen/briefs/$k/L4; X=$R/output/studio_cal/$k
cd $R
$O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev || exit 1
$R/tools/heavy.sh 8 $O build $L --assets $R/assets_dev --out $X/a7_xbuild > $X/a7_xbuild.log 2>&1 || { tail -3 $X/a7_xbuild.log; exit 1; }
ROOT=${ROOT:-$R/output/studio_cal/a7/root_s6}
$R/tools/heavy.sh 8 $O install $L --root $ROOT --build $X/a7_xbuild > $X/a7_xinstall.log 2>&1 || { tail -3 $X/a7_xinstall.log; exit 1; }
$R/tools/heavy.sh 8 $O audit $ROOT/worlds/xeen/maps/xeen_$k.blv --world xeen --assets $ROOT --reach --solve > $X/a7_xaudit.txt 2>&1
echo "$k: build warnings $(grep -c '^warning' $X/a7_xbuild.log); audit:"; grep -E "^(error|warning)" $X/a7_xaudit.txt | cut -c1-230
