#!/bin/bash
# XD-17 into a fresh hard-link stage of assets_dev (world data tables a real copy, the map's files unlinked), the
# build installed there, the audit and the playtests (N each, default 2); then (INSTALL=1, all runs passed) the map's
# files into assets_dev by new file + rename. KEEP=1 keeps the stage. Build first: output/studio_cal/xd17/b.sh.
# Usage: [INSTALL=1] [N=2] level_generation/projects/xeen/xd17/stage_install.sh
export OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -uo pipefail
cd "$OYR"
X=output/studio_cal/xd17; st=$X/stage_$$
OY=openyamm-studio/build-xeen/oymap
FILES="maps/xeen_xd17.blv maps/xeen_xd17.scene.yml maps/xeen_xd17.studio.yml events/maps/xeen_xd17.lua
terrain_materials/xeen_xd17_blv.yml terrain_materials/xeen_xd17_blv_weights0.png"
mkdir -p $st; cp -al assets_dev $st/assets_dev; S=$st/assets_dev
python3 - "$S" $FILES <<'PY'
import os, shutil, sys
S = os.path.realpath(sys.argv[1])
assert '/output/studio_cal/xd17/stage_' in S
X = os.path.join(S, 'worlds/xeen')
shutil.rmtree(os.path.join(X, 'data_tables'))
shutil.copytree(os.environ['OYR'] + '/assets_dev/worlds/xeen/data_tables', os.path.join(X, 'data_tables'))
for f in sys.argv[2:]:
    p = os.path.join(X, f)
    if os.path.exists(p):
        os.remove(p)
PY
$OY install devdocs/xeen/briefs/xd17/L4 --root $S --build $X/build | tee $X/stage_install.log
$OY audit xeen_xd17.blv --world xeen --assets $S --reach --solve --dressing > $X/audit_stage.txt 2>&1
grep -E "^error" $X/audit_stage.txt && echo "audit errors"
N=${N:-2} ASSETS=$PWD/$S bash $OYR/level_generation/projects/xeen/xd17/run_tests.sh | tee $X/stage_tests.log
total=$(grep -c ' run ' $X/stage_tests.log); ok=$(grep -c 'exit 0' $X/stage_tests.log)
echo "stage: $ok of $total runs passed"
if [ "$ok" != "$total" ] || [ "${INSTALL:-0}" != 1 ]; then echo "not installed; stage: $st"; exit 0; fi
D=assets_dev/worlds/xeen
for f in $FILES; do
  [ -f $S/worlds/xeen/$f ] || continue
  cmp -s $S/worlds/xeen/$f $D/$f && { echo "unchanged $f"; continue; }
  cp $S/worlds/xeen/$f $D/$f.new; chmod 0644 $D/$f.new; mv -f $D/$f.new $D/$f; echo "installed $f $(date +%H:%M:%S)"
done
if [ "${KEEP:-0}" != 1 ]; then
python3 - "$st" <<'PY'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert os.path.basename(t).startswith('stage_') and t.startswith(os.environ['OYR'] + '/output/studio_cal/xd17/')
shutil.rmtree(t); print('stage removed', t)
PY
fi
