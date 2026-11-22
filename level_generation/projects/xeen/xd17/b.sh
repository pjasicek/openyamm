#!/bin/bash
# Build XD-17's L4 into output/studio_cal/xd17/build (against ASSETS, default assets_dev); install into ROOT if given.
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${ASSETS:-assets_dev}
OY=$PWD/openyamm-studio/build-xeen/oymap
level_generation/projects/xeen/xd17/v.sh $ASSETS | grep -v "no issues\|^==\|valley floor points" || true
python3 -c "import shutil,os; p='output/studio_cal/xd17/build.new'; os.path.isdir(p) and shutil.rmtree(p)"
$OY build devdocs/xeen/briefs/xd17/L4 --out output/studio_cal/xd17/build.new --assets $ASSETS > output/studio_cal/xd17/build.log 2>&1 || { cut -c1-400 output/studio_cal/xd17/build.log | tail -30; exit 1; }
python3 -c "import shutil,os; p='output/studio_cal/xd17/build'; os.path.isdir(p) and shutil.rmtree(p); os.rename(p+'.new', p)"
cut -c1-300 output/studio_cal/xd17/build.log | tail -30
$OY fmt devdocs/xeen/briefs/xd17/L4 > /dev/null
if [ -n "$ROOT" ]; then $OY install devdocs/xeen/briefs/xd17/L4 --root $ROOT --build output/studio_cal/xd17/build | tail -3; fi
