#!/bin/bash
# Build D7 L4 into output/studio_cal/d7/build (against ASSETS, default the scratch root), playtests regenerated from the
# build's ids.lock.yml, then install into the scratch root only (never assets_dev).
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${ASSETS:-output/studio_cal/d7/root/assets_dev}
OY=$PWD/openyamm-studio/build-xeen/oymap
X=output/studio_cal/d7
level_generation/projects/xeen/d7/v.sh $ASSETS | grep -v "no issues\|^==" || true
$OY build devdocs/xeen/briefs/d7/L4 --out $X/build --assets $ASSETS > $X/build.log 2>&1 || { cut -c1-300 $X/build.log; exit 1; }
cut -c1-260 $X/build.log
systemd-run --user --scope -q -p MemoryMax=8G python3 level_generation/projects/xeen/d7/gen_playtests.py
$OY fmt devdocs/xeen/briefs/d7/L4 > /dev/null
if [ "$ASSETS" = output/studio_cal/d7/root/assets_dev ]; then
  $OY install devdocs/xeen/briefs/d7/L4 --root $ASSETS --build $X/build > $X/install_root.log 2>&1 && tail -3 $X/install_root.log
fi
