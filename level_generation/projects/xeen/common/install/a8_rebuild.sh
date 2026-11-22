#!/bin/bash
# Lane A8: fmt, validate, build an L4 against assets_dev into output/studio_cal/<key>/b_<time>, stage it with
# `oymap install --mount` and (INSTALL=1) copy the map's four files into assets_dev by temp file and rename.
# rebuild.sh <key>    e.g. INSTALL=1 rebuild.sh xd12
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; k=$1; L=$R/devdocs/xeen/briefs/$k/L4
X=$R/output/studio_cal/$k; T=$(date +%H%M%S); B=$X/b_$T
cd $R
$O fmt $L >/dev/null; $O fmt --check $L || exit 1
$O validate $L --assets $R/assets_dev | tail -1
$R/tools/heavy.sh 8 $O build $L --assets $R/assets_dev --out $B/build > $B.build.log 2>&1 || { tail -5 $B.build.log; exit 1; }
tail -1 $B.build.log
$R/tools/heavy.sh 8 $O install $L --mount $B/stage --assets $R/assets_dev --build $B/build > /dev/null || exit 1
echo "built and staged: $B"
[ "${INSTALL:-0}" = 1 ] && python3 $R/level_generation/projects/xeen/common/install/install_stage.py xeen_$k $B/stage
exit 0
