#!/bin/bash
# Regenerate P1's L2-L4 and check them (fmt, validate). Usage: level_generation/projects/xeen/p1/v.sh [assets root]
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${1:-output/studio_cal/p1/root}
OY=$PWD/openyamm-studio/build-xeen/oymap
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
$CAP python3 level_generation/projects/xeen/p1/gen.py > output/studio_cal/p1/gen.out
for L in L2 L3 L4; do
  $OY fmt devdocs/xeen/briefs/p1/$L > /dev/null
  echo "== validate $L"; $OY validate devdocs/xeen/briefs/p1/$L --assets $ASSETS 2>&1 | cut -c1-400 | tail -25
done
