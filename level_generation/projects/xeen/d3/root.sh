#!/bin/bash
# A5 (2026-11-20, seventh session): D3's scratch game root for tours and headless checks until A2 writes D3's map_stats
# and travel rows and A4 its houses: a hard-link copy of assets_dev (the game reads no symlinked file) with D3's build
# installed into it (oymap install --root) and two tables replaced by new files (unlinked first, so assets_dev's inodes
# are never written): map_stats.txt (+ D3's row as project.yml says it) and outdoor_travels.txt (D3 west <-> D2 east).
# Remove the old root first by its literal path. Usage: root.sh
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
C=$PWD/output/studio_cal/d3
R=$C/root
if [ -e $R ]; then echo "$R exists: remove it first"; exit 1; fi
cp -al assets_dev $R
for f in maps/xeen_d3.odm maps/xeen_d3.scene.yml maps/xeen_d3.studio.yml maps/xeen_d3.lighting maps/xeen_d3.bake.json \
         events/maps/xeen_d3.lua; do rm -f "$R/worlds/xeen/$f"; done
openyamm-studio/build-xeen/oymap install devdocs/xeen/briefs/d3/L4 --build $C/build_w --root $R > $C/run/root_install.log 2>&1
python3 - "$R/worlds/xeen/data_tables" <<'PY'
import os, sys
d = sys.argv[1]
ROW = ('9110\tSandcaster and the Aging Forest\txeen_d3.odm\t0\t0\t3\t672\t0\t0\t8\t4\t4\t10\t50\t26\t24\t'
       'Xeen Mantis\tXeen Mantis\t1\t 2-3\tXeen Cobra\tXeen Cobra\t1\t 2-3\tXeen Sand Worm\tXeen Sand Worm\t1\t 2-3\t'
       '39\tFOREST\tmap_studio\t0\t0\t-\t')
TRAVEL = 'xeen_d3.odm' + '\t' * 7 + 'xeen_d2.odm\tleft\t5\t\t\t\t\tSandcaster and the Aging Forest\t\t\t\t\t'
def rewrite(name, fix):
    path = os.path.join(d, name)
    text = open(path, encoding='latin-1').read()
    os.remove(path)
    with open(path, 'w', encoding='latin-1') as f:
        f.write(fix(text))
rewrite('map_stats.txt', lambda t: t if '\txeen_d3.odm\t' in t else t.rstrip('\n') + '\n' + ROW + '\n')
def travel(t):
    out = []
    for line in t.rstrip('\n').split('\n'):
        c = line.split('\t')
        if c[0] == 'xeen_d2.odm' and len(c) > 12 and not c[10]:
            c[10:13] = ['xeen_d3.odm', 'right', '5']
            line = '\t'.join(c)
        out.append(line)
    if not any(l.startswith('xeen_d3.odm\t') for l in out):
        out.append(TRAVEL)
    return '\n'.join(out) + '\n'
rewrite('outdoor_travels.txt', travel)
PY
grep -n "xeen_d[23]" $R/worlds/xeen/data_tables/outdoor_travels.txt | cut -c1-120
echo "root: $R"
