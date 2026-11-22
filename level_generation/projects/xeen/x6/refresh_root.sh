#!/bin/bash
# A5: put X6's current build into the scratch root made by root.sh (new files only), its tables and terrain weights.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
C=$PWD/output/studio_cal/x6
R=$C/root
for f in maps/xeen_x6.odm maps/xeen_x6.scene.yml maps/xeen_x6.studio.yml events/maps/xeen_x6.lua; do rm -f "$R/worlds/xeen/$f"; done
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/x6/L4 --build $C/build_w --root $R > $C/run/root_install.log 2>&1
python3 $OYR/level_generation/projects/xeen/x6/root_tables.py $R
python3 tools/terrain_materials.py weights --world xeen --map xeen_x6.odm --assets $R > $C/run/root_weights.log 2>&1
echo "root refreshed"
