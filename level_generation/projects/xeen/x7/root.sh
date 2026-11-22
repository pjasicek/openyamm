#!/bin/bash
# A5 (2026-11-20): X7's scratch game root for the walk, hostility and tour while the studio refuses `lavtyl` (the
# build_w build is then l4_check's: lava as water, a check only, never installed). A hard-link copy of assets_dev (the
# game reads no symlinked file) whose data tables and terrain materials are real copies (the rules: tables copied,
# never hard-linked; terrain_materials.py writes into the copy), X7's build installed into it (oymap install --root)
# and its terrain weights. A2's map_stats row 9105 is in the copied table. Remove the old root first by its literal
# path: rm -rf $OYR/output/studio_cal/x7/root      Usage: root.sh
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
R=$OYR/output/studio_cal/x7/root
if [ -e $R ]; then echo "$R exists: remove it first"; exit 1; fi
cp -al assets_dev $R
rm -rf $OYR/output/studio_cal/x7/root/worlds/xeen/data_tables
cp -r assets_dev/worlds/xeen/data_tables $R/worlds/xeen/data_tables
rm -rf $OYR/output/studio_cal/x7/root/worlds/xeen/terrain_materials
cp -r assets_dev/worlds/xeen/terrain_materials $R/worlds/xeen/terrain_materials
P=devdocs/xeen/briefs/x7/L4
[ -e output/studio_cal/x7/l4_check/sketch.yml ] && P=output/studio_cal/x7/l4_check
openyamm-studio/build-xeen/oymap install $P --build output/studio_cal/x7/build_w --root $R \
  > output/studio_cal/x7/run/root_install.log 2>&1
python3 tools/terrain_materials.py weights --world xeen --map xeen_x7.odm --assets $R \
  > output/studio_cal/x7/run/root_weights.log 2>&1
echo "root: $R (project $P)"
