#!/bin/bash
# A5 (2026-11-20, seventh session): D3 in the Xeen world. Generate L1-L4 (tools/gen.py, which runs gen_l1.py), fmt,
# validate, build into build_w, measure, dressing check. Install only through level_generation/projects/xeen/common/install/a5_install_baked.sh:
#   level_generation/projects/xeen/common/install/a5_install_baked.sh xeen_d3 devdocs/xeen/briefs/d3/L4 output/studio_cal/d3/build_w \
#       level_generation/projects/xeen/d3/bake_profile.json
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/d3
P=$B/L4
C=output/studio_cal/d3
mkdir -p $C/run
python3 level_generation/projects/xeen/d3/gen.py $B > $C/run/gen_w.log
for L in L1 L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L1 L2 L3; do $O validate $B/$L --assets assets_dev > $C/run/validate_$L.txt 2>&1 || { echo "validate $L failed"; tail -30 $C/run/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev > $C/run/validate_w.log 2>&1 || { tail -40 $C/run/validate_w.log; exit 1; }
$O build $P --assets assets_dev --out $C/build_w > $C/run/build_w.log 2>&1 || { tail -30 $C/run/build_w.log; exit 1; }
python3 level_generation/projects/xeen/x2/check_d85.py $C/build_w/xeen_d3.scene.yml > $C/run/d85.txt || { grep -E '^ERROR' $C/run/d85.txt; echo 'D-85/D-87 check failed'; exit 1; }   # A5 s27 (D-87)
grep -E "^warning|^built" $C/run/build_w.log | grep -v "faces in one plane" | cut -c1-300
python3 level_generation/projects/xeen/d3/measure.py $C/build_w $P || true
python3 level_generation/projects/xeen/x1/dress_check.py $C/build_w xeen_d3 || true
# A5 s29 (F10, F16 audits): empty zones and the audit on every build
python3 tools/xeen/empty_zones.py --check --scene output/studio_cal/d3/build_w/xeen_d3.scene.yml --lua output/studio_cal/d3/build_w/xeen_d3.lua > output/studio_cal/d3/run/empty_zones.txt || { sed -n 3,8p output/studio_cal/d3/run/empty_zones.txt; echo "empty zones: a zone larger than the MM6-MM8 maps typical one (F10)"; }
openyamm-studio/build-xeen/oymap audit devdocs/xeen/briefs/d3/L4 --assets assets_dev --reach --solve --textures > output/studio_cal/d3/run/audit_w.txt 2>&1 || true
