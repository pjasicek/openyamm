#!/bin/bash
# DD-07: generate, fmt, validate, build, install into the scratch root, audit (--reach --solve). cycle.sh [--no-gen]
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/dd07/L4
X=$R/output/studio_cal/dd07; ROOT=$X/root
cd $R
[ "$1" = "--no-gen" ] || python3 level_generation/projects/xeen/dd07/gen.py L4 || exit 1   # L4 only since D-58 (s17): L1-L3 stay as approved
for lv in L1 L2 L3 L4; do $O fmt $R/devdocs/xeen/briefs/dd07/$lv >/dev/null; done
$O validate $L --assets $R/assets_dev > $X/validate.log 2>&1 || { tail -40 $X/validate.log; exit 1; }
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -40 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_dd07.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-300
