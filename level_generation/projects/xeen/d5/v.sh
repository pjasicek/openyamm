#!/bin/bash
# A6 (2026-11-20): D5 Desert of Doom. Generate L2-L4 (tools/gen.py), fmt, validate, build into build,
# measure, dressing check, audit. Install and bake: level_generation/projects/xeen/common/install/a6_install_baked.sh.
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/d5
P=$B/L4
C=output/studio_cal/d5
mkdir -p $C/run
python3 level_generation/projects/xeen/d5/gen.py $B > $C/run/gen.log
for L in L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L2 L3; do $O validate $B/$L --assets assets_dev > $C/run/validate_$L.txt 2>&1 || { echo "validate $L failed"; tail -30 $C/run/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev > $C/run/validate.log 2>&1 || { tail -40 $C/run/validate.log; exit 1; }
$O build $P --assets assets_dev --out $C/build > $C/run/build.log 2>&1 || { tail -30 $C/run/build.log; exit 1; }
grep -E "^warning|^built" $C/run/build.log | grep -v "faces in one plane" | cut -c1-300
python3 level_generation/projects/xeen/d5/measure.py $C/build $P || true
python3 level_generation/projects/xeen/x1/measure.py $C/build $P | grep -E "quiet|hostiles|encounter|chests|open meadow" || true
python3 level_generation/projects/xeen/x1/dress_check.py $C/build xeen_d5 || true
