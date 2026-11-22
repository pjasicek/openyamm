#!/bin/bash
# Regenerate XD-17's L2-L4 and check them (fmt, validate). Usage: level_generation/projects/xeen/xd17/v.sh [assets root]
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ASSETS=${1:-assets_dev}
OY=$PWD/openyamm-studio/build-xeen/oymap
systemd-run --user --scope -q -p MemoryMax=8G python3 level_generation/projects/xeen/xd17/gen.py > /dev/null
for L in L2 L3 L4; do
  $OY fmt devdocs/xeen/briefs/xd17/$L > /dev/null
  echo "== validate $L"; $OY validate devdocs/xeen/briefs/xd17/$L --assets $ASSETS 2>&1 | cut -c1-500 | tail -40
done
