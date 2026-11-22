#!/bin/bash
# A7 warnings pass: fmt, validate, build to output/studio_cal/<key>/w_build, install into a7w/root, audit. wcycle.sh xd05
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; k=$1; L=$R/devdocs/xeen/briefs/$k/L4; X=$R/output/studio_cal/$k
ROOT=$R/output/studio_cal/a7w/root
cd $R
$O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev || exit 1
$R/tools/heavy.sh 8 $O build $L --assets $R/assets_dev --out $X/w_build > $X/w_build.log 2>&1 || { tail -3 $X/w_build.log; exit 1; }
$R/tools/heavy.sh 8 $O install $L --root $ROOT --build $X/w_build > $X/w_install.log 2>&1 || { tail -3 $X/w_install.log; exit 1; }
$R/tools/heavy.sh 8 $O audit $ROOT/worlds/xeen/maps/xeen_$k.blv --world xeen --assets $ROOT --reach --solve > $X/w_audit.txt 2>&1
echo "$k: build warnings $(grep -c '^warning' $X/w_build.log); audit:"; grep -E "^(error|warning)" $X/w_audit.txt | cut -c1-230
