#!/bin/bash
# A5 (2026-11-20): X6's scratch game root for the walk, hostility and tour until A2 writes X6's map_stats row 9104 and
# A4 un-plans x6.yml (house rows 4301-4305): a hard-link copy of assets_dev (the game reads no symlinked file) with X6's
# build installed into it (oymap install --root) and two tables replaced by new files (unlinked first, so assets_dev's
# inodes are never written): map_stats.txt (+ X6's stand-in row as project.yml says it) and edge_spans.yml (X6's east
# and south edges to X4 and X5 as project.yml says, and X4's west and X5's north edges back to X6's starts, so the walk
# crosses both ways). Remove the old root first by its literal path. Usage: root.sh
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
C=$PWD/output/studio_cal/x6
R=$C/root
if [ -e $R ]; then echo "$R exists: remove it first"; exit 1; fi
cp -al assets_dev $R
for f in maps/xeen_x6.odm maps/xeen_x6.scene.yml maps/xeen_x6.studio.yml maps/xeen_x6.lighting maps/xeen_x6.bake.json \
         events/maps/xeen_x6.lua; do rm -f "$R/worlds/xeen/$f"; done
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/x6/L4 --build $C/build_w --root $R > $C/run/root_install.log 2>&1
python3 $OYR/level_generation/projects/xeen/x6/root_tables.py $R
python3 tools/terrain_materials.py weights --world xeen --map xeen_x6.odm --assets $R > $C/run/root_weights.log 2>&1
echo "root: $R"
