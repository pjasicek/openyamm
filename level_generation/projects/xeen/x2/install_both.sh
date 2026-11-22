#!/bin/bash
# Install X1 and X2 into X2's mount so that both travel rows stand: each install copies the asset root's tables and
# writes its own row, so the second install would lose the first's; the rows are merged here (scratch mount only).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
cd "$OYR"
O=openyamm-studio/build/oymap
C=output/studio_cal/x2
$O install devdocs/xeen/briefs/x1/L4 --build $C/x1_build --mount $C/mount --assets output/studio_play/xeen_root > $C/x1_install.txt
grep -P "^xeen_x1\.odm\t" $C/mount/engine/data_tables/outdoor_travels.txt > $C/x1_row.txt
$O install devdocs/xeen/briefs/x2/L4 --build $C/build --mount $C/mount --assets output/studio_play/xeen_root > $C/install.txt
python3 - <<'PY'
p='output/studio_cal/x2/mount/engine/data_tables/outdoor_travels.txt'
row=open('output/studio_cal/x2/x1_row.txt').read().rstrip('\n')
lines=open(p).read().split('\n')
lines=[row if l.startswith('xeen_x1.odm\t') else l for l in lines]
open(p+'.new','w').write('\n'.join(lines))
import os; os.replace(p+'.new', p)
PY
python3 openyamm-studio/calibration/outdoor_materials.py devdocs/xeen/briefs/x1/L4 --mount $C/mount --build $C/x1_build > /dev/null
python3 openyamm-studio/calibration/outdoor_materials.py devdocs/xeen/briefs/x2/L4 --mount $C/mount --build $C/build > /dev/null
grep -P "^xeen_x[12]\.odm\t" $C/mount/engine/data_tables/outdoor_travels.txt
