#!/bin/bash
# DD-26: generate (gen.py), fmt, validate, build to output/studio_cal/dd26/build, install into the scratch root, audit
# (--reach --solve), record. LEVELS="L1 L2 L3 L4" regenerates the earlier levels too; INSTALL=0 stops after the build.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; X=$R/output/studio_cal/dd26; B=$R/devdocs/xeen/briefs/dd26
L=$B/L4; ROOT=${ROOT:-$X/root}
cd $R
python3 level_generation/projects/xeen/dd26/gen.py ${LEVELS:-L4} || exit 1
for lv in ${LEVELS:-L4}; do $O fmt $B/$lv >/dev/null; done
for lv in ${LEVELS:-L4}; do echo "== validate $lv"; $O validate $B/$lv --assets $R/assets_dev 2>&1 | grep -v "^note: the asset root"; done
$O build $L --assets $R/assets_dev --out $X/build > $X/build.log 2>&1 || { grep -E "^error" $X/build.log | head -30; tail -3 $X/build.log; exit 1; }
echo "build warnings: $(grep -c '^warning' $X/build.log)"; grep "^warning" $X/build.log | cut -c1-250
[ "${INSTALL:-1}" = 1 ] || exit 0
for f in $ROOT/worlds/xeen/maps/xeen_dd26.blv $ROOT/worlds/xeen/maps/xeen_dd26.scene.yml $ROOT/worlds/xeen/events/maps/xeen_dd26.lua; do
  [ -e $f ] && [ "$(stat -c %h $f)" != 1 ] && { echo "refusing: $f is hard-linked"; exit 1; }
done
$O install $L --root $ROOT --build $X/build > $X/install.log 2>&1 || { tail -5 $X/install.log; exit 1; }
$O audit $ROOT/worlds/xeen/maps/xeen_dd26.blv --world xeen --assets $ROOT --reach --solve > $X/audit.txt 2>&1
echo "audit:"; grep -E "^(error|warning)" $X/audit.txt | cut -c1-250
[ "${RECORD:-1}" = 1 ] && $O record $L --author agent:xeen-a8-dd26 --label "${LABEL:-generator run}" >/dev/null
true
