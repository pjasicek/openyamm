#!/bin/bash
# Build X9 L4 into output/studio_cal/x9/build (against ASSETS, default assets_dev); playtests regenerated from the
# build's ids.lock.yml. Install separately (stage_install.sh).
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${ASSETS:-assets_dev}
OY=$PWD/openyamm-studio/build-xeen/oymap
X=output/studio_cal/x9
level_generation/projects/xeen/x9/v.sh $ASSETS | grep -v "no issues\|^==" || true
$OY build devdocs/xeen/briefs/x9/L4 --out $X/build --assets $ASSETS > $X/build.log 2>&1 || { cut -c1-300 $X/build.log; exit 1; }
python3 level_generation/projects/xeen/x2/check_d85.py $X/build/xeen_x9.scene.yml > $X/d85.txt || { grep -E '^ERROR' $X/d85.txt; echo 'D-85/D-87 check failed'; exit 1; }   # A5 s27 (D-87)
cut -c1-260 $X/build.log
systemd-run --user --scope -q -p MemoryMax=8G python3 level_generation/projects/xeen/x9/gen_playtests.py
$OY fmt devdocs/xeen/briefs/x9/L4 > /dev/null
