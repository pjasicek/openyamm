#!/bin/bash
# The scratch root output/studio_cal/p4/root: a hard-link copy of assets_dev; worlds/xeen/data_tables and world.yml
# copied (never hard-linked), xeen_p4.blv added to the copy's openAirMaps. Rerun to refresh from assets_dev.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
python3 - <<'PY'
import os, shutil
R = os.path.realpath('output/studio_cal/p4/root'); assert R.endswith('/output/studio_cal/p4/root')
if os.path.exists(R):
    shutil.rmtree(R)
PY
cp -al assets_dev output/studio_cal/p4/root
python3 - <<'PY'
import os, shutil
R = os.path.realpath('output/studio_cal/p4/root'); assert R.endswith('/output/studio_cal/p4/root')
X = os.path.join(R, 'worlds/xeen')
shutil.rmtree(os.path.join(X, 'data_tables'))
shutil.copytree('assets_dev/worlds/xeen/data_tables', os.path.join(X, 'data_tables'))
os.remove(os.path.join(X, 'world.yml'))
s = open('assets_dev/worlds/xeen/world.yml').read()
pass
open(os.path.join(X, 'world.yml'), 'w').write(s if 'xeen_p4.blv' in s else s.replace('openAirMaps:\n', 'openAirMaps:\n  - xeen_p4.blv\n', 1))
for f in ('maps/xeen_p4.blv', 'maps/xeen_p4.scene.yml', 'maps/xeen_p4.studio.yml', 'maps/xeen_p4.cinematics.yml',
          'events/maps/xeen_p4.lua'):
    if os.path.exists(os.path.join(X, f)):
        os.remove(os.path.join(X, f))
for line in open(os.path.join(X, 'data_tables/map_stats.txt')):
    if line.startswith('9118\t'):
        print(line[:110])
print('root ready', R)
PY
