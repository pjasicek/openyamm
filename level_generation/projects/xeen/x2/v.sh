#!/bin/bash
# Regenerate the X2 project (and L1-L3) from tools/gen.py, format, validate, build into the scratch folder, install
# into X2's own mount in front of output/studio_play/xeen_root, write the terrain material file there.
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build-xeen/oymap
B=devdocs/xeen/briefs/x2
P=$B/L4
C=output/studio_cal/x2
python3 level_generation/projects/xeen/x2/gen.py $B
for L in L1 L2 L3 L4; do $O fmt $B/$L > /dev/null; done
for L in L1 L2 L3; do $O validate $B/$L --assets assets_dev > $C/validate_$L.txt 2>&1 || { echo "validate $L failed"; cat $C/validate_$L.txt; exit 1; }; done
$O validate $P --assets assets_dev
$O build $P --assets assets_dev --out $C/build "$@"
$C/install_both.sh
