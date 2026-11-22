#!/bin/bash
# D7 into a hard-link stage of assets_dev, its playtests there (N each, default 2), then (INSTALL=1) its files into
# assets_dev by new file + rename. KEEP=1 keeps the stage. The world.yml openAirMaps entry is the orchestrator's: the
# stage adds xeen_d7.blv to its own copy only; install only once assets_dev's world.yml lists it.
# Usage: [INSTALL=1] level_generation/projects/xeen/d7/stage_install.sh   (the lead runs it)
export OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -uo pipefail
cd "$OYR"
X=output/studio_cal/d7; st=$X/stage_$$
mkdir -p $st; cp -al assets_dev $st/assets_dev; S=$st/assets_dev
python3 - "$S" <<'PY'
import os, shutil, sys
S = os.path.realpath(sys.argv[1])
assert '/output/studio_cal/d7/stage_' in S
X = os.path.join(S, 'worlds/xeen')
shutil.rmtree(os.path.join(X, 'data_tables'))
shutil.copytree(os.environ['OYR'] + '/assets_dev/worlds/xeen/data_tables', os.path.join(X, 'data_tables'))
w = open(os.environ['OYR'] + '/assets_dev/worlds/xeen/world.yml').read()
os.remove(os.path.join(X, 'world.yml'))
if 'xeen_d7.blv' not in w:
    w = w.replace('openAirMaps:\n', 'openAirMaps:\n  - xeen_d7.blv\n', 1)
open(os.path.join(X, 'world.yml'), 'w').write(w)
for f in ('maps/xeen_d7.blv', 'maps/xeen_d7.scene.yml', 'maps/xeen_d7.studio.yml', 'events/maps/xeen_d7.lua'):
    p = os.path.join(X, f)
    if os.path.exists(p):
        os.remove(p)
PY
ASSETS=$S bash $OYR/level_generation/projects/xeen/d7/b.sh
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/d7/L4 --root $S --build $X/build | tee $X/stage_install.log
openyamm-studio/build-xeen/oymap audit xeen_d7.blv --world xeen --assets $S > $X/audit_stage.txt 2>&1
grep -E "^error" $X/audit_stage.txt && echo "audit errors"
N=${N:-2} ASSETS=$PWD/$S bash $OYR/level_generation/projects/xeen/d7/tests.sh | tee $X/stage_tests.log
total=$(grep -c ' run ' $X/stage_tests.log); ok=$(grep -c 'exit 0' $X/stage_tests.log)
echo "stage: $ok of $total runs passed"
if [ "$ok" != "$total" ] || [ "${INSTALL:-0}" != 1 ]; then echo "not installed; stage: $st"; exit 0; fi
grep -q 'xeen_d7.blv' assets_dev/worlds/xeen/world.yml || { echo "assets_dev world.yml lacks xeen_d7.blv in openAirMaps (orchestrator): not installed"; exit 0; }
D=assets_dev/worlds/xeen
for f in maps/xeen_d7.blv maps/xeen_d7.scene.yml maps/xeen_d7.studio.yml events/maps/xeen_d7.lua; do
  [ -f $S/worlds/xeen/$f ] || continue
  cp $S/worlds/xeen/$f $D/$f.new; chmod 0644 $D/$f.new; mv -f $D/$f.new $D/$f; echo "installed $f $(date +%H:%M)"
done
if [ "${KEEP:-0}" != 1 ]; then
python3 - "$st" <<'PY'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert os.path.basename(t).startswith('stage_') and t.startswith(os.environ['OYR'] + '/output/studio_cal/d7/')
shutil.rmtree(t); print('stage removed', t)
PY
fi
