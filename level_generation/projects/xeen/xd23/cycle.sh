#!/bin/bash
# XD-23: regenerate, fmt, validate, build, install into the scratch root, audit --reach --solve (agent:xeen-a7-xd23)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd23/L4; X=$R/output/studio_cal/xd23
ROOT=$X/root
cd $R
python3 level_generation/projects/xeen/xd23/gen.py || exit 1
$O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev || exit 1
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -15 $X/build.log; exit 1; }
python3 level_generation/projects/xeen/xd23/gen.py >/dev/null && $O fmt $L >/dev/null   # the sound numbers from the fresh ids.lock.yml
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { tail -15 $X/build.log; exit 1; }
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_xd23.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
$O fmt --check $L > /dev/null 2>&1 && echo "fmt clean" || echo "fmt NOT clean"
echo "build warnings $(grep -c '^warning' $X/build.log); audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-260
