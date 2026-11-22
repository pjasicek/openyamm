#!/bin/bash
# A6 D4: a pre-test stage (hard-link copy of assets_dev, the world's data tables copied, never linked) with the current
# build installed and its terrain weights written; no bake. Usage: a6_stage_map.sh <key>   (remakes
# output/studio_cal/<key>/stage/)
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../../../.."
K=$1
C=output/studio_cal/$K
S=$C/stage/assets_dev
K=$K python3 - <<'PY'
import os, shutil
K = os.environ['K']
t = 'output/studio_cal/'+K+'/stage'
if os.path.isdir(t):
    shutil.rmtree(t)
os.makedirs(t)
PY
cp -al assets_dev $S
K=$K python3 - <<'PY'
import os, shutil
K = os.environ['K']
W = 'output/studio_cal/'+K+'/stage/assets_dev/worlds/xeen'
shutil.rmtree(W + '/data_tables')
shutil.copytree('assets_dev/worlds/xeen/data_tables', W + '/data_tables')
for f in os.listdir(W + '/terrain_materials'):
    if f.startswith('xeen_'+K+''):
        os.unlink(W + '/terrain_materials/' + f)
for f in ('maps/xeen_'+K+'.odm', 'maps/xeen_'+K+'.scene.yml', 'maps/xeen_'+K+'.studio.yml', 'maps/xeen_'+K+'.lighting',
          'maps/xeen_'+K+'.bake.json', 'events/maps/xeen_'+K+'.lua'):
    if os.path.exists(W + '/' + f):
        os.unlink(W + '/' + f)
PY
tools/heavy.sh 8 openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/$K/L4 --build $C/build --root $S > $C/run/stage_install.log
tools/heavy.sh 8 python3 tools/terrain_materials.py weights --world xeen --map xeen_$K.odm --assets $S > $C/run/stage_weights.log
echo
echo staged
