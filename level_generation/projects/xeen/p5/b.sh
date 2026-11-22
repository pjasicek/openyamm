#!/bin/bash
# Build P5 L4 into output/studio_cal/p5/build (against ASSETS, default the scratch root); playtests regenerated from
# the build's ids.lock.yml. Install separately (stage_install.sh).
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${ASSETS:-output/studio_cal/p5/root}
OY=$PWD/openyamm-studio/build-xeen/oymap
X=output/studio_cal/p5
level_generation/projects/xeen/p5/v.sh $ASSETS | grep -v "no issues\|^==" || true
$OY build devdocs/xeen/briefs/p5/L4 --out $X/build --assets $ASSETS > $X/build.log 2>&1 || { cut -c1-300 $X/build.log; exit 1; }
cut -c1-260 $X/build.log
systemd-run --user --scope -q -p MemoryMax=8G python3 level_generation/projects/xeen/p5/gen_playtests.py
$OY fmt devdocs/xeen/briefs/p5/L4 > /dev/null
# into the scratch root only (never assets_dev): the map's files are new files there (setup_root.sh unlinks them)
if [ "$ASSETS" = output/studio_cal/p5/root ]; then
  $OY install devdocs/xeen/briefs/p5/L4 --root $ASSETS --build $X/build > $X/install_root.log 2>&1 && tail -3 $X/install_root.log
fi
