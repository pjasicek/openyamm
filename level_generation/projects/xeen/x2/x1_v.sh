#!/bin/bash
# X1 rebuilt as output/studio_cal/x1/v.sh does, but into X2's scratch build (x1_build) and X2's mount (so X1 and X2
# see each other's travel rows); X1's own build outputs and the shared xeen_root are left alone.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
cd "$OYR"
O=openyamm-studio/build/oymap
P=devdocs/xeen/briefs/x1/L4
C=output/studio_cal/x2
python3 level_generation/projects/xeen/x1/gen.py $P
$O fmt $P
$O validate $P --assets assets_dev
$O build $P --assets assets_dev --out $C/x1_build "$@"
$OYR/level_generation/projects/xeen/x2/install_both.sh
python3 level_generation/projects/xeen/x1/gen_walk.py $P $C/x1_build
