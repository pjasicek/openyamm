#!/bin/bash
# Regenerate D7's L2-L4 and check them (fmt, validate). Usage: level_generation/projects/xeen/d7/v.sh [assets root]
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${1:-output/studio_cal/d7/root/assets_dev}
OY=$PWD/openyamm-studio/build-xeen/oymap
X=level_generation/projects/xeen/d7
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
$CAP python3 $X/gen.py > output/studio_cal/d7/gen.out
$CAP python3 $X/gen_plan.py >> output/studio_cal/d7/gen.out
$CAP python3 $X/gen_objects.py >> output/studio_cal/d7/gen.out
cp devdocs/xeen/briefs/d7/L4/atmosphere.yml devdocs/xeen/briefs/d7/L3/
cp devdocs/xeen/briefs/d7/L1/atmosphere.yml devdocs/xeen/briefs/d7/L2/
for L in L2 L3 L4; do
  $OY fmt devdocs/xeen/briefs/d7/$L > /dev/null
  echo "== validate $L"; $OY validate devdocs/xeen/briefs/d7/$L --assets $ASSETS 2>&1 | cut -c1-400 | tail -25
done
