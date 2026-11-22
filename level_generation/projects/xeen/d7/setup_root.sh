#!/bin/bash
# The scratch root output/studio_cal/d7/root/assets_dev: a hard-link copy of assets_dev; worlds/xeen/data_tables and
# world.yml copied (never hard-linked), xeen_d7.blv added to the copy's openAirMaps (the orchestrator's entry in
# assets_dev). A2's map_stats row 9114 is in assets_dev since 2026-11-21 (no scratch row). Rerun to refresh.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
python3 - <<'PY'
import os, shutil
R = os.path.realpath('output/studio_cal/d7/root'); assert R.endswith('/output/studio_cal/d7/root')
if os.path.exists(R):
    shutil.rmtree(R)
os.makedirs(R)
PY
cp -al assets_dev output/studio_cal/d7/root/assets_dev
python3 - <<'PY'
import os, shutil
R = os.path.realpath('output/studio_cal/d7/root/assets_dev'); assert R.endswith('/output/studio_cal/d7/root/assets_dev')
X = os.path.join(R, 'worlds/xeen')
shutil.rmtree(os.path.join(X, 'data_tables'))
shutil.copytree('assets_dev/worlds/xeen/data_tables', os.path.join(X, 'data_tables'))
os.remove(os.path.join(X, 'world.yml'))
s = open('assets_dev/worlds/xeen/world.yml').read()
if 'xeen_d7.blv' not in s:
    assert 'openAirMaps:\n' in s
    s = s.replace('openAirMaps:\n', 'openAirMaps:\n  - xeen_d7.blv\n', 1)
open(os.path.join(X, 'world.yml'), 'w').write(s)
for f in ('maps/xeen_d7.blv', 'maps/xeen_d7.scene.yml', 'maps/xeen_d7.studio.yml', 'events/maps/xeen_d7.lua'):
    if os.path.exists(os.path.join(X, f)):
        os.remove(os.path.join(X, f))
ok = any(l.startswith('9114\t') for l in open(os.path.join(X, 'data_tables/map_stats.txt')))
print('root ready', R, 'map_stats 9114', ok)
PY
