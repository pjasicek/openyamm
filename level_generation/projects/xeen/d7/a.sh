#!/bin/bash
# Audit D7: the L4 project (the lanes' full set) and the map installed in the scratch root (as the game reads it).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
cd "$OYR"
ASSETS=${ASSETS:-output/studio_cal/d7/root/assets_dev}
OY=openyamm-studio/build-xeen/oymap
$OY audit devdocs/xeen/briefs/d7/L4 --world xeen --assets $ASSETS --reach --solve --dressing --lights --doors --textures > output/studio_cal/d7/audit.txt 2>&1
echo "project audit exit $? errors $(grep -c '^error' output/studio_cal/d7/audit.txt) warnings $(grep -c '^warning' output/studio_cal/d7/audit.txt)"
$OY audit xeen_d7.blv --world xeen --assets $ASSETS > output/studio_cal/d7/audit_root.txt 2>&1
echo "installed audit exit $? errors $(grep -c '^error' output/studio_cal/d7/audit_root.txt) warnings $(grep -c '^warning' output/studio_cal/d7/audit_root.txt)"
grep -h -v '^info' output/studio_cal/d7/audit.txt output/studio_cal/d7/audit_root.txt | cut -c1-260 | head -${N:-40}
