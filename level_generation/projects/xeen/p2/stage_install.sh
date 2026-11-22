#!/bin/bash
# P2 into a hard-link stage of assets_dev, its playtests there (N each, default 2), then (INSTALL=1) its files into
# assets_dev by new file + rename. KEEP=1 keeps the stage. Not to be run until the blockers are cleared (L4 NOTES,
# "Open items"), and the world.yml openAirMaps entry is the orchestrator's (the stage adds it to its own copy only).
# Usage: [INSTALL=1] level_generation/projects/xeen/p2/stage_install.sh
export OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -uo pipefail
cd "$OYR"
X=output/studio_cal/p2; st=$X/stage_$$
mkdir -p $st; cp -al assets_dev $st/assets_dev; S=$st/assets_dev
python3 - "$S" <<'PY'
import os, shutil, sys
S = os.path.realpath(sys.argv[1])
assert '/output/studio_cal/p2/stage_' in S
X = os.path.join(S, 'worlds/xeen')
shutil.rmtree(os.path.join(X, 'data_tables'))
shutil.copytree(os.environ['OYR'] + '/assets_dev/worlds/xeen/data_tables', os.path.join(X, 'data_tables'))
w = open(os.environ['OYR'] + '/assets_dev/worlds/xeen/world.yml').read()
os.remove(os.path.join(X, 'world.yml'))
if 'xeen_p2.blv' not in w:
    w = w.replace('openAirMaps:\n', 'openAirMaps:\n  - xeen_p2.blv\n', 1)
open(os.path.join(X, 'world.yml'), 'w').write(w)
for f in ('maps/xeen_p2.blv', 'maps/xeen_p2.scene.yml', 'maps/xeen_p2.studio.yml',
          'events/maps/xeen_p2.lua'):
    p = os.path.join(X, f)
    if os.path.exists(p):
        os.remove(p)
PY
ASSETS=$S bash $OYR/level_generation/projects/xeen/p2/b.sh
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/p2/L4 --root $S --build $X/build | tee $X/stage_install.log
openyamm-studio/build-xeen/oymap audit xeen_p2.blv --world xeen --assets $S > $X/audit_stage.txt 2>&1
grep -E "^error" $X/audit_stage.txt && echo "audit errors"
N=${N:-2} ASSETS=$PWD/$S bash $OYR/level_generation/projects/xeen/p2/run.sh | tee $X/stage_tests.log
total=$(grep -c ' run ' $X/stage_tests.log); ok=$(grep -c 'exit 0' $X/stage_tests.log)
echo "stage: $ok of $total runs passed"
if [ "$ok" != "$total" ] || [ "${INSTALL:-0}" != 1 ]; then echo "not installed; stage: $st"; exit 0; fi
D=assets_dev/worlds/xeen
for f in maps/xeen_p2.blv maps/xeen_p2.scene.yml maps/xeen_p2.studio.yml events/maps/xeen_p2.lua; do
  [ -f $S/worlds/xeen/$f ] || continue
  cp $S/worlds/xeen/$f $D/$f.new; chmod 0644 $D/$f.new; mv -f $D/$f.new $D/$f; echo "installed $f $(date +%H:%M)"
done
if [ "${KEEP:-0}" != 1 ]; then
python3 - "$st" <<'PY'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert os.path.basename(t).startswith('stage_') and t.startswith(os.environ['OYR'] + '/output/studio_cal/p2/')
shutil.rmtree(t); print('stage removed', t)
PY
fi
