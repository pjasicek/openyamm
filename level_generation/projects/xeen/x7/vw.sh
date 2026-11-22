#!/bin/bash
# A5 (2026-11-20): X7 in the Xeen world. Generate L2-L4 (tools/gen.py; L1 is the approved plan, untouched), fmt,
# validate, build into build_w, measure, dressing check, audit. Install only through level_generation/projects/xeen/common/install/a5_install_baked.sh
# (and only once `oymap validate` takes `tile_set: lavtyl` and A2's map_stats row 9105 exists):
#   bash level_generation/projects/xeen/common/install/a5_install_baked.sh xeen_x7 devdocs/xeen/briefs/x7/L4 output/studio_cal/x7/build_w \
#       level_generation/projects/xeen/x7/bake_profile.json
# While the oymap refuses `lavtyl` (A1's lava set is in the tile table but not yet in the studio binary), the build and
# its checks run on a scratch copy of L4 whose lava bodies lose `tile_set` (plain water): output/studio_cal/x7/l4_check.
# That copy is a check only and is never installed (no stand-ins in anything called done).
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/x7
P=$B/L4
C=output/studio_cal/x7
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
mkdir -p $C/run
$CAP python3 level_generation/projects/xeen/x7/gen.py $B > $C/run/gen_w.log || { cat $C/run/gen_w.log; exit 1; }
cat $C/run/gen_w.log
for L in L2 L3 L4; do $O fmt $B/$L > /dev/null; done
$O fmt --check $B/L1 > /dev/null || echo "L1 not formatted"
$O validate $B/L2 --assets assets_dev > $C/run/validate_L2.txt 2>&1 || { echo "validate L2 failed"; tail -30 $C/run/validate_L2.txt; exit 1; }
if $O validate $P --assets assets_dev > $C/run/validate_w.log 2>&1; then
  echo "L4 validates (lava as lavtyl)"
  rm -rf output/studio_cal/x7/l4_check
else
  if grep -v "lavtyl" $C/run/validate_w.log | grep -q "yml"; then
    tail -40 $C/run/validate_w.log; exit 1
  fi
  echo "L4 refused only for lavtyl (A1's studio binary): checking on $C/l4_check (lava as water, never installed)"
  rm -rf $C/l4_check
  mkdir -p $C/l4_check
  cp $P/*.yml $C/l4_check/
  python3 - "$C/l4_check/sketch.yml" <<'EOF'
import sys
p = sys.argv[1]
lines = [l for l in open(p) if l.strip() != 'tile_set: lavtyl']
open(p, 'w').writelines(lines)
EOF
  P=$C/l4_check
  $O validate $P --assets assets_dev > $C/run/validate_check.log 2>&1 || { tail -40 $C/run/validate_check.log; exit 1; }
fi
$O build $P --assets assets_dev --out $C/build_w > $C/run/build_w.log 2>&1 || { tail -30 $C/run/build_w.log; exit 1; }
python3 level_generation/projects/xeen/x2/check_d85.py $C/build_w/xeen_x7.scene.yml > $C/run/d85.txt || { grep -E '^ERROR' $C/run/d85.txt; echo 'D-85/D-87 check failed'; exit 1; }   # A5 s27 (D-87)
grep -E "^warning|^built" $C/run/build_w.log | grep -v "faces in one plane" | cut -c1-300 || true
[ "$P" != "$B/L4" ] && cp $P/ids.lock.yml $B/L4/ids.lock.yml 2>/dev/null || true
$CAP python3 level_generation/projects/xeen/x7/measure.py $C/build_w $P || true
python3 tools/xeen/empty_zones.py --check --scene $C/build_w/xeen_x7.scene.yml --lua $C/build_w/xeen_x7.lua || echo 'empty zones: a zone larger than the MM6-MM8 maps typical one (F10)'   # F10
python3 level_generation/projects/xeen/x1/dress_check.py $C/build_w xeen_x7 || true
$O audit $P --assets assets_dev --reach --solve --textures > $C/run/audit_w.txt 2>&1 || true
tail -5 $C/run/audit_w.txt
