#!/bin/bash
# A6 D5: a pre-test stage (hard-link copy of assets_dev, the world's data tables copied, never linked) with the current
# build installed and its terrain weights written; no bake. Usage: stage.sh   (removes and remakes stage/)
export OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
C=output/studio_cal/d5
S=$C/stage/assets_dev
python3 - <<'PY'
import os, shutil
t = os.environ['OYR'] + '/output/studio_cal/d5/stage'
if os.path.isdir(t):
    shutil.rmtree(t)
os.makedirs(t)
PY
cp -al assets_dev $S
python3 - <<'PY'
import os, shutil
W = os.environ['OYR'] + '/output/studio_cal/d5/stage/assets_dev/worlds/xeen'
shutil.rmtree(W + '/data_tables')
shutil.copytree(os.environ['OYR'] + '/assets_dev/worlds/xeen/data_tables', W + '/data_tables')
for f in os.listdir(W + '/terrain_materials'):
    if f.startswith('xeen_d5'):
        os.unlink(W + '/terrain_materials/' + f)
for f in ('maps/xeen_d5.odm', 'maps/xeen_d5.scene.yml', 'maps/xeen_d5.studio.yml', 'maps/xeen_d5.lighting',
          'maps/xeen_d5.bake.json', 'events/maps/xeen_d5.lua'):
    if os.path.exists(W + '/' + f):
        os.unlink(W + '/' + f)
PY
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/d5/L4 --build $C/build --root $S > $C/run/stage_install.log
python3 tools/terrain_materials.py weights --world xeen --map xeen_d5.odm --assets $S > $C/run/stage_weights.log
grep -c 9112 $S/worlds/xeen/data_tables/map_stats.txt || echo "no 9112 row in the stage"
echo staged
