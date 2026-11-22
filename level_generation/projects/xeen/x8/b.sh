#!/bin/bash
# Build X8 L4 into output/studio_cal/x8/build and install it into the scratch root (or ROOT=...).
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
ROOT=${ROOT:-output/studio_cal/x8/root}
OY=$PWD/openyamm-studio/build-xeen/oymap
level_generation/projects/xeen/x8/v.sh $ROOT | grep -v "no issues\|^==\|^arrivals\|^monsters" || true
$OY build devdocs/xeen/briefs/x8/L4 --out output/studio_cal/x8/build --assets $ROOT > output/studio_cal/x8/build.log 2>&1 || { cut -c1-300 output/studio_cal/x8/build.log; exit 1; }
grep -v "rests on nothing" output/studio_cal/x8/build.log | cut -c1-260
python3 level_generation/projects/xeen/x8/gen_playtests.py
$OY fmt devdocs/xeen/briefs/x8/L4 > /dev/null
$OY install devdocs/xeen/briefs/x8/L4 --root $ROOT --build output/studio_cal/x8/build | tail -1
