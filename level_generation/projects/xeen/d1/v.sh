#!/bin/bash
# A6 (2026-11-20): D1 Castleview Vale. Generate L2-L4 (tools/gen.py), fmt, validate, build into build, measure,
# dressing check. With --install: install into assets_dev, the terrain weights (look.sh/present/bake.sh do the rest).
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/d1
P=$B/L4
C=output/studio_cal/d1
mkdir -p $C/run
python3 level_generation/projects/xeen/d1/gen.py $B > $C/run/gen.log || { cat $C/run/gen.log; exit 1; }
for L in L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L2 L3; do $O validate $B/$L --assets assets_dev > $C/run/validate_$L.txt 2>&1 || { echo "validate $L failed"; tail -30 $C/run/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev > $C/run/validate.log 2>&1 || { tail -40 $C/run/validate.log; exit 1; }
$O build $P --assets assets_dev --out $C/build > $C/run/build.log 2>&1 || { tail -30 $C/run/build.log; exit 1; }
grep -E "^warning|^built" $C/run/build.log | grep -v "faces in one plane" | cut -c1-300
python3 level_generation/projects/xeen/x1/dress_check.py $C/build xeen_d1 || true
python3 level_generation/projects/xeen/d1/gate_check.py $C/build || exit 1
if [ "$1" = "--install" ]; then
  $O install $P --build $C/build --root assets_dev > $C/run/install.log
  python3 tools/terrain_materials.py weights --world xeen --map xeen_d1.odm > $C/run/weights.log
fi
