#!/bin/bash
# A6 (2026-11-20): D2 Sprite Forest and Ogre Pass. Generate L2-L4 (tools/gen.py), fmt, validate, build into build,
# measure, dressing check, audit. Install and bake: present/install_bake.sh.
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/d2
P=$B/L4
C=output/studio_cal/d2
mkdir -p $C/run
python3 level_generation/projects/xeen/d2/gen.py $B > $C/run/gen.log
for L in L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L2 L3; do $O validate $B/$L --assets assets_dev > $C/run/validate_$L.txt 2>&1 || { echo "validate $L failed"; tail -30 $C/run/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev > $C/run/validate.log 2>&1 || { tail -40 $C/run/validate.log; exit 1; }
$O build $P --assets assets_dev --out $C/build > $C/run/build.log 2>&1 || { tail -30 $C/run/build.log; exit 1; }
grep -E "^warning|^built" $C/run/build.log | grep -v "faces in one plane" | cut -c1-300
python3 level_generation/projects/xeen/d2/measure.py $C/build $P || true
python3 level_generation/projects/xeen/x1/measure.py $C/build $P | grep -E "quiet|hostiles|encounter|chests|open meadow" || true
python3 level_generation/projects/xeen/x1/dress_check.py $C/build xeen_d2 || true
# D-85/D-87 and D-15's first fight (D-133): D-136 keeps Q-D11's fort camps (groups 1, 2: melee ogres guarding the
# DD-13 gates from outside) at the gates' arrivals
python3 level_generation/projects/xeen/x2/check_d85.py $C/build/xeen_d2.scene.yml --kept-group 1 --kept-group 2 > $C/run/d85.txt || { grep -E '^ERROR' $C/run/d85.txt; echo 'D-85/D-87 check failed'; exit 1; }
