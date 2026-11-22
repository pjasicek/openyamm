#!/bin/bash
# A6 ninth session: X8 into a hard-link stage, its five playtests there, then its files into assets_dev (new + rename).
export OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
X=output/studio_cal/x8; st=$X/stage_$$
mkdir -p $st; cp -al assets_dev $st/assets_dev; S=$st/assets_dev
python3 - "$S" <<'PY'
import os, shutil, sys
S = os.path.realpath(sys.argv[1])
assert '/output/studio_cal/x8/stage_' in S
t = os.path.join(S, 'worlds/xeen/data_tables')
shutil.rmtree(t)
shutil.copytree(os.environ['OYR'] + '/assets_dev/worlds/xeen/data_tables', t)
for f in ('maps/xeen_x8.blv', 'maps/xeen_x8.scene.yml', 'maps/xeen_x8.studio.yml', 'events/maps/xeen_x8.lua'):
    p = os.path.join(S, 'worlds/xeen', f)
    if os.path.exists(p):
        os.remove(p)
PY
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/x8/L4 --root $S --build $X/build | tee $X/stage_install.log
flock output/studio_cal/a6/locks/game1.lock env ASSETS=$PWD/$S bash $OYR/level_generation/projects/xeen/x8/run.sh | tee $X/stage_tests.log
if [ "$(grep -c 'exit 0' $X/stage_tests.log)" != 5 ]; then echo "tests failed; stage kept: $st"; exit 1; fi
D=assets_dev/worlds/xeen
for f in maps/xeen_x8.blv maps/xeen_x8.scene.yml maps/xeen_x8.studio.yml events/maps/xeen_x8.lua; do
  [ -f $S/worlds/xeen/$f ] || continue
  cp $S/worlds/xeen/$f $D/$f.new; chmod 0644 $D/$f.new; mv -f $D/$f.new $D/$f; echo "installed $f"
done
python3 - "$st" <<'PY'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert os.path.basename(t).startswith('stage_') and t.startswith(os.environ['OYR'] + '/output/studio_cal/x8/')
shutil.rmtree(t); print('stage removed', t)
PY
