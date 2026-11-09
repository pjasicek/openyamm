#!/bin/bash
# Runs every probe_*.yml in parallel; writes <name>.log and prints the actor's track.
cd /home/pjasicek/github/OpenYAMM
D=level_generation/projects/mm9r_drangheimprison/reach
for f in $D/probe_*.yml; do
  n=$(basename $f .yml)
  ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario "$PWD/$f" --scenario-no-color > $D/$n.log 2>&1 &
done
wait
python3 - <<'PY'
import re,glob,os
for f in sorted(glob.glob('level_generation/projects/mm9r_drangheimprison/reach/probe_*.log')):
    track=[]; end=''
    for l in open(f,errors='replace'):
        m=re.search(r'ACTOR index=\d+ .*position=(\S+) .*animation=(\d+) hostile=(\w+) targeting_party=(\w+) aim_target=(\w+)',l)
        if m: track.append(m.group(1)+('*' if m.group(4)=='true' else ''))
        if l.startswith('Scenario failure') or l.startswith('Scenario passed'): end=l.strip()[:190]
    print(os.path.basename(f)[6:-4],' '.join(track)); print('   ',end)
PY
