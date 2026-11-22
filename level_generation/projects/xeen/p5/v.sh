#!/bin/bash
# Regenerate P5's L2-L4 and check them (fmt, validate). Usage: level_generation/projects/xeen/p5/v.sh [assets root]
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${1:-assets_dev}
OY=$PWD/openyamm-studio/build-xeen/oymap
X=level_generation/projects/xeen/p5
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
$CAP python3 $X/gen.py > output/studio_cal/p5/gen.out
$CAP python3 $X/gen_plan.py > /dev/null
$CAP python3 $X/gen_objects.py >> output/studio_cal/p5/gen.out
cp devdocs/xeen/briefs/p5/L4/atmosphere.yml devdocs/xeen/briefs/p5/L3/
for L in L2 L3 L4; do
  $OY fmt devdocs/xeen/briefs/p5/$L > /dev/null
  echo "== validate $L"; $OY validate devdocs/xeen/briefs/p5/$L --assets $ASSETS 2>&1 | cut -c1-400 | tail -25
done
