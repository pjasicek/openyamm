#!/bin/bash
# Regenerate X8's L2-L4 and check them (validate, fmt). Usage: level_generation/projects/xeen/x8/v.sh [assets root]
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${1:-output/studio_cal/x8/root}
OY=$PWD/openyamm-studio/build-xeen/oymap
python3 level_generation/projects/xeen/x8/gen.py > /dev/null
python3 level_generation/projects/xeen/x8/gen_plan.py > /dev/null
python3 level_generation/projects/xeen/x8/gen_objects.py
cp devdocs/xeen/briefs/x8/L4/atmosphere.yml devdocs/xeen/briefs/x8/L3/
for L in L2 L3 L4; do
  $OY fmt devdocs/xeen/briefs/x8/$L > /dev/null
  echo "== validate $L"; $OY validate devdocs/xeen/briefs/x8/$L --assets $ASSETS 2>&1 | cut -c1-400 | tail -25
done
