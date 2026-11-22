#!/bin/bash
# Audit P5's L4 project against the scratch root (or ASSETS): the lanes' full set.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
cd "$OYR"
ASSETS=${ASSETS:-output/studio_cal/p5/root}
openyamm-studio/build-xeen/oymap audit devdocs/xeen/briefs/p5/L4 --world xeen --assets $ASSETS --reach --solve --dressing --lights --doors --textures > output/studio_cal/p5/audit.txt 2>&1
echo "audit exit $? errors $(grep -c '^error' output/studio_cal/p5/audit.txt) warnings $(grep -c '^warning' output/studio_cal/p5/audit.txt)"
grep -v '^info' output/studio_cal/p5/audit.txt | cut -c1-260 | head -${N:-30}
