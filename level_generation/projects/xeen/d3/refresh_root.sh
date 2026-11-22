#!/bin/bash
# A5: put D3's current build into the scratch root made by root.sh (new files only) and its terrain weights.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
C=$PWD/output/studio_cal/d3
R=$C/root
for f in maps/xeen_d3.odm maps/xeen_d3.scene.yml maps/xeen_d3.studio.yml events/maps/xeen_d3.lua; do rm -f "$R/worlds/xeen/$f"; done
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/d3/L4 --build $C/build_w --root $R > $C/run/root_install.log 2>&1
python3 tools/terrain_materials.py weights --world xeen --map xeen_d3.odm --assets $R > $C/run/root_weights.log 2>&1
echo "root refreshed"
