#!/bin/bash
# Make XD-17's stage: a hard-link copy of assets_dev in output/studio_cal/xd17/stage/assets_dev, the world's
# data_tables a real copy (never links), the map's own files unlinked; then install the build into it.
export OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
S=output/studio_cal/xd17/stage/assets_dev
if [ ! -d $S ]; then
  mkdir -p output/studio_cal/xd17/stage
  cp -al assets_dev $S
  python3 - <<'PY'
import os, shutil
S = os.path.realpath('output/studio_cal/xd17/stage/assets_dev')
assert S.endswith('/output/studio_cal/xd17/stage/assets_dev')
t = os.path.join(S, 'worlds/xeen/data_tables')
shutil.rmtree(t)
shutil.copytree(os.environ['OYR'] + '/assets_dev/worlds/xeen/data_tables', t)
PY
fi
python3 - <<'PY'
import os
S = os.path.realpath('output/studio_cal/xd17/stage/assets_dev/worlds/xeen')
for f in ('maps/xeen_xd17.blv', 'maps/xeen_xd17.scene.yml', 'maps/xeen_xd17.studio.yml', 'events/maps/xeen_xd17.lua',
          'terrain_materials/xeen_xd17_blv.yml', 'terrain_materials/xeen_xd17_blv_weights0.png'):
    p = os.path.join(S, f)
    if os.path.exists(p):
        os.remove(p)
PY
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/xd17/L4 --root $S --build output/studio_cal/xd17/build | tail -5
