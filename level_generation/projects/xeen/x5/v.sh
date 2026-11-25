#!/bin/bash
# A6 (2026-11-20): X5 Winterkill Tundra. Generate L2-L4 (tools/gen.py), fmt, validate, build into build, measure,
# dressing check. With --install: install into assets_dev and write the terrain material weights.
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/x5
P=$B/L4
C=output/studio_cal/x5
mkdir -p $C/run
python3 level_generation/projects/xeen/x5/gen.py $B > $C/run/gen.log
for L in L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L2 L3; do $O validate $B/$L --assets assets_dev > $C/run/validate_$L.txt 2>&1 || { echo "validate $L failed"; tail -30 $C/run/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev > $C/run/validate.log 2>&1 || { tail -40 $C/run/validate.log; exit 1; }
$O build $P --assets assets_dev --out $C/build > $C/run/build.log 2>&1 || { tail -30 $C/run/build.log; exit 1; }
grep -E "^warning|^built" $C/run/build.log | grep -v "faces in one plane" | cut -c1-300
python3 level_generation/projects/xeen/x1/measure.py $C/build $P | grep -v "^ \|per central cell" || true
python3 level_generation/projects/xeen/x1/dress_check.py $C/build xeen_x5 || true
# D-85/D-87 and D-15's first fight (D-133): givers at 5,120 (D-87 (4)); D-136 keeps group 40 (Q-C6's first wave by the
# square, D-13, D-87) at the arrivals; Mayor Randon (NPC 4502) stands among it by D-87.1: his giver line is that rule's
python3 level_generation/projects/xeen/x2/check_d85.py $C/build/xeen_x5.scene.yml 5120 --kept-group 40 --kept-giver 4502 > $C/run/d85.txt || true
if grep -E '^ERROR' $C/run/d85.txt | grep -v '^ERROR npc 4502 '; then echo 'D-85/D-87 check failed'; exit 1; fi
if [ "$1" = "--install" ]; then
  $O install $P --build $C/build --root assets_dev
  python3 tools/terrain_materials.py weights --world xeen --map xeen_x5.odm
  # the liquid edges are the world's, shared with X1/X2: regenerate them only after telling xeen-o (2026-11-20)
fi
