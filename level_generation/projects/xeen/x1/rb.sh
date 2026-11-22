#!/bin/bash
# Rebase (A5, 2026-11-20): regenerate the X1 project, fmt, validate, build into build_rb, measure.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
cd "$OYR"
O=openyamm-studio/build-xeen/oymap
P=devdocs/xeen/briefs/x1/L4
C=output/studio_cal/x1
python3 $OYR/level_generation/projects/xeen/x1/gen.py $P > $C/run/gen_rb.log
$O fmt $P > /dev/null
$O validate $P --assets assets_dev > $C/run/validate_rb.log 2>&1 || { tail -20 $C/run/validate_rb.log; exit 1; }
$O build $P --assets assets_dev --out $C/build_rb > $C/run/build_rb.log 2>&1 || { tail -20 $C/run/build_rb.log; exit 1; }
python3 level_generation/projects/xeen/x2/check_d85.py $C/build_rb/xeen_x1.scene.yml > $C/run/d85.txt || { grep -E '^ERROR' $C/run/d85.txt; echo 'D-85/D-87 check failed'; exit 1; }   # A5 s27 (D-87)
grep -E "^warning|^built" $C/run/build_rb.log | grep -v "faces in one plane" | cut -c1-400
python3 $OYR/level_generation/projects/xeen/x1/measure.py $C/build_rb $P
if [ "$1" = "--root" ]; then
  $O install $P --build $C/build_rb --root $C/xroot > /dev/null
  python3 openyamm-studio/calibration/outdoor_materials.py $P --root $C/xroot --build $C/build_rb > /dev/null
  python3 openyamm-studio/calibration/town_feel.py $C/xroot/worlds/mm7/maps/xeen_x1.odm --world mm7 --assets $C/xroot > $C/run/town_feel_rb.txt 2>&1
  grep "OUT\|figure" $C/run/town_feel_rb.txt
fi
# A5 s29 (F10, F16 audits): empty zones and the audit on every build
python3 tools/xeen/empty_zones.py --check --scene $C/build_rb/xeen_x1.scene.yml --lua $C/build_rb/xeen_x1.lua > $C/run/empty_zones.txt || { cat $C/run/empty_zones.txt; echo "empty zones: a zone larger than the MM6-MM8 maps typical one (F10)"; }
mkdir -p $C/run && $O audit $P --assets assets_dev --reach --solve --textures > $C/run/audit_w.txt 2>&1 || true
