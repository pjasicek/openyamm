#!/bin/bash
# Regenerate the X1 project from tools/gen.py, format, validate, build into the scratch folder.
set -e
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
O=openyamm-studio/build/oymap
P=devdocs/xeen/briefs/x1/L4
C=output/studio_cal/x1
python3 level_generation/projects/xeen/x1/gen.py $P
$O fmt $P
$O validate $P --assets assets_dev
$O build $P --assets assets_dev --out $C/build "$@"
$O install $P --build $C/build --root $C/root > /dev/null
python3 openyamm-studio/calibration/outdoor_materials.py $P --root $C/root --build $C/build > /dev/null
python3 level_generation/projects/xeen/x1/gen_walk.py $P $C/build
