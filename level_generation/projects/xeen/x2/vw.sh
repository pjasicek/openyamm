#!/bin/bash
# A5 (2026-11-20): X2 in the Xeen world. Generate L1-L4 (tools/gen.py, IN_WORLD), fmt, validate, build into build_w,
# measure, dressing check. With --install: install into assets_dev and write the terrain material weights.
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/x2
P=$B/L4
C=output/studio_cal/x2
mkdir -p $C/run
python3 level_generation/projects/xeen/x2/gen.py $B > $C/run/gen_w.log
for L in L1 L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L1 L2 L3; do $O validate $B/$L --assets assets_dev > $C/validate_$L.txt 2>&1 || { echo "validate $L failed"; tail -20 $C/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev > $C/run/validate_w.log 2>&1 || { tail -20 $C/run/validate_w.log; exit 1; }
$O build $P --assets assets_dev --out $C/build_w > $C/run/build_w.log 2>&1 || { tail -20 $C/run/build_w.log; exit 1; }
grep -E "^warning|^built" $C/run/build_w.log | grep -v "faces in one plane" | cut -c1-300
python3 level_generation/projects/xeen/x1/measure.py $C/build_w $P | grep -v "^ \|xd0\|yard\|per central cell"
python3 level_generation/projects/xeen/x1/dress_check.py $C/build_w xeen_x2
python3 level_generation/projects/xeen/x2/check_d85.py $C/build_w/xeen_x2.scene.yml --kept-group 63 > $C/run/d85.txt || { grep -E "^ERROR" $C/run/d85.txt; echo "D-85/D-87 check failed"; exit 1; }   # A5 s26; s27 (D-87); s28 (D-88): only the temple guards (group 63) waived
python3 tools/xeen/empty_zones.py --check --scene $C/build_w/xeen_x2.scene.yml --lua $C/build_w/xeen_x2.lua > $C/run/empty_zones.txt || { cat $C/run/empty_zones.txt; echo "empty zones: a zone larger than the MM6-MM8 maps typical one (F10)"; exit 1; }   # A5 s29 (F10)
$O audit $P --assets assets_dev --reach --solve --textures > $C/run/audit_w.txt 2>&1 || true   # A5 s29
grep -c "^error" $C/run/audit_w.txt || true
if [ "$1" = "--install" ]; then
  $O install $P --build $C/build_w --root assets_dev
  bash level_generation/projects/xeen/common/install/terrain_swap.sh xeen_x2   # private root, then swapped in (A5, fifth session)
fi
