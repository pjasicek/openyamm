#!/bin/bash
# Build P1 L4 into output/studio_cal/p1/build (against ASSETS, default the scratch root); playtests regenerated from the
# build's ids.lock.yml and scene; into the scratch root only (never assets_dev).
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${ASSETS:-output/studio_cal/p1/root}
OY=$PWD/openyamm-studio/build-xeen/oymap
X=output/studio_cal/p1
level_generation/projects/xeen/p1/v.sh $ASSETS | grep -v "no issues\|^==" || true
$OY build devdocs/xeen/briefs/p1/L4 --out $X/build --assets $ASSETS > $X/build.log 2>&1 || { cut -c1-300 $X/build.log; exit 1; }
cut -c1-260 $X/build.log
systemd-run --user --scope -q -p MemoryMax=8G python3 level_generation/projects/xeen/p1/gen_playtests.py
$OY fmt devdocs/xeen/briefs/p1/L4 > /dev/null
if [ "$ASSETS" = output/studio_cal/p1/root ]; then
  $OY install devdocs/xeen/briefs/p1/L4 --root $ASSETS --build $X/build > $X/install_root.log 2>&1 && tail -1 $X/install_root.log
  $OY audit xeen_p1.blv --world xeen --assets $ASSETS > $X/audit.txt 2>&1; head -4 $X/audit.txt | cut -c1-200
fi
