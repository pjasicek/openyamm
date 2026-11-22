#!/bin/bash
# XD-08: generate, fmt, validate, build, install into the scratch root, audit (--reach --solve).
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd08/L4; X=$R/output/studio_cal/xd08
ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd08/gen.py || exit 1
for l in L1 L2 L3 L4; do $O fmt $R/devdocs/xeen/briefs/xd08/$l >/dev/null; $O validate $R/devdocs/xeen/briefs/xd08/$l --assets $R/assets_dev | grep -v 'no issues'; done
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -5 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -3 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd08.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "build warnings $(grep -c '^warning' $X/build.log); $(tail -1 $X/build.log)"; grep '^warning' $X/build.log | cut -c1-260
echo "audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
